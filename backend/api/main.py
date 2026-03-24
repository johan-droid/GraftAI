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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis

from backend.auth.routes import router as auth_router
from backend.api.users import router as users_router
from backend.services.ai import router as ai_router
from backend.services.analytics import router as analytics_router
from backend.services.consent import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade import router as upgrade_router
from backend.services.plugin_api import router as plugin_router

# Rate limiting setup
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


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
        
        # Check rate limit
        client = _get_redis_client()
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        current = client.get(key)
        if current is None:
            client.setex(key, self.window, 1)
        elif int(current) >= self.max_requests:
            # Rate limit exceeded
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
            await response(scope, receive, send)
            return
        else:
            client.incr(key)
        
        await self.app(scope, receive, send)


# Parse rate limit from env
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")

app = FastAPI(
    title="GraftAI Backend",
    description="Production API for GraftAI — AI-powered scheduling platform",
    version="1.0.0",
)

# Add rate limiting middleware BEFORE CORS
app.add_middleware(RateLimitMiddleware, rate_limit=_rate_limit_str)

# CORS — read allowed origins from env, fallback to local dev + production frontend
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://graft-ai-two.vercel.app")
_frontend_url = os.getenv("FRONTEND_BASE_URL")

_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
if _frontend_url:
    _cors_origins.append(_frontend_url.strip())

# Remove duplicates while preserving order
_cors_origins = list(dict.fromkeys(_cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ──
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(consent_router)
app.include_router(proactive_router)
app.include_router(upgrade_router)
app.include_router(plugin_router)


from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase


@app.on_event("startup")
async def create_database_tables():
    if not db_utils.engine:
        logger.warning("⚠ Database engine is not configured; skipping auto-migration.")
        return
    try:
        async with db_utils.engine.begin() as conn:
            await conn.run_sync(ModelsBase.metadata.create_all)
        print("✅ Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"⚠ Failed to create or verify database tables: {type(e).__name__}")


@app.get("/")
def root():
    return {"message": "GraftAI Backend API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}
