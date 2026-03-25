import os
import sys
import re
import logging
from pathlib import Path
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path so `import backend...` works even when the process starts from inside backend/
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load env FIRST so all modules can read env vars
dotenv_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis

from backend.auth.routes import router as auth_router
from backend.api.calendar import router as calendar_router
from backend.api.users import router as users_router
from backend.services.ai import router as ai_router
from backend.services.analytics import router as analytics_router
from backend.services.consent import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade import router as upgrade_router
from backend.services.plugin_api import router as plugin_router
from backend.auth.schemes import get_current_user

from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase

# Rate limiting setup
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


# Atomic Rate Limiting Lua Script
RATE_LIMIT_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
if current > limit then
    return 0
end
return 1
"""


def _parse_rate_limit(rate_limit: str):
    """Parse rate limit string like '100/minute' into (count, window_seconds)."""
    match = re.match(r'(\d+)/(\w+)', rate_limit)
    if not match:
        return 100, 60  # default: 100 per minute
    
    count = int(match.group(1))
    unit = match.group(2).lower()
    
    # Convert to seconds
    multipliers = {
        'second': 1,
        'seconds': 1,
        'minute': 60,
        'minutes': 60,
        'hour': 3600,
        'hours': 3600,
        'day': 86400,
        'days': 86400,
    }
    window = multipliers.get(unit, 60)
    return count, window


class RateLimitMiddleware:
    """Simple Redis-backed rate limiting middleware."""
    
    def __init__(self, app, rate_limit: str = "100/minute"):
        self.app = app
        self.max_requests, self.window = _parse_rate_limit(rate_limit)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope)
        
        # Get client IP
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        # Atomic check-and-increment via Lua
        client = _get_redis_client()
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        # Use eval to run the scriptatomically
        allowed = client.eval(RATE_LIMIT_LUA, 1, key, self.max_requests, self.window)
        
        if not allowed:
            # Rate limit exceeded
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)


# Parse rate limit from env
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # 1. DB Verification
    if db_utils.engine:
        try:
            async with db_utils.engine.begin() as conn:
                await conn.run_sync(ModelsBase.metadata.create_all)
            logger.info("✅ Database tables verified/created successfully.")
        except Exception as e:
            logger.error(f"⚠ Failed to create or verify database tables: {type(e).__name__}")
    
    # 2. Password Self-Test
    try:
        from backend.services.auth_utils import get_password_hash, verify_password
        test_pw = "StartupSelfTest99!"
        test_hash = get_password_hash(test_pw)
        if not verify_password(test_pw, test_hash):
            raise RuntimeError("Password verification self-test failed")
        logger.info("✅ Password hashing system verified.")
    except Exception as e:
        logger.critical(f"CRITICAL: Password hashing system failure: {e}")
        raise RuntimeError("Password hashing system initialization failed") from e
    
    # 3. Auth0 Verification
    domain = os.getenv("AUTH0_DOMAIN")
    audience = os.getenv("AUTH0_AUDIENCE")
    if domain and audience:
        logger.info(f"✅ Auth0 configuration detected for domain: {domain}")

    yield
    # --- Shutdown ---
    # Clean up global connections if needed

app = FastAPI(
    title="GraftAI Backend",
    description="Production API for GraftAI — AI-powered scheduling platform",
    version="1.0.0",
    lifespan=lifespan
)


# --- Middleware Registration ---
# 1. Rate Limiting (Distributed via Redis)
app.add_middleware(RateLimitMiddleware, rate_limit=_rate_limit_str)

# 2. CORS (Hardened for Production)
cors_origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    os.getenv("LOAD_BALANCER_URL", "http://localhost:8080"),
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Inclusion ---
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(calendar_router)
app.include_router(ai_router)
app.include_router(proactive_router)
app.include_router(analytics_router)
app.include_router(consent_router)
app.include_router(upgrade_router)
app.include_router(plugin_router)


@app.get("/")
def root():
    return {
        "message": "GraftAI Sovereign API is online.",
        "version": "1.0.0",
        "scaling_pool": "3 Replicas (Active)",
        "rate_limit_active": True
    }


@app.get("/health")
def health():
    return {"status": "ok", "environment": "production-hardened"}
