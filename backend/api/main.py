import os
import sys
import re
import uuid
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path so `import backend...` works correctly regardless of execution context
project_root = Path(__file__).resolve().parents[2] # Root directory (parent of backend/)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load env FIRST so all modules can read env vars
dotenv_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Request, Depends, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis

from backend.auth.routes import router as auth_router
from backend.api.calendar import router as calendar_router
from backend.api.users import router as users_router
from backend.api.uploads import router as uploads_router
from backend.services.ai import router as ai_router
from backend.services.analytics import router as analytics_router
from backend.services.consent import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade import router as upgrade_router
from backend.services.plugin_api import router as plugin_router
from backend.api.notifications import router as notifications_router
from backend.api.billing import router as billing_router
from backend.utils.db import get_db

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
    match = re.match(r"(\d+)/(\w+)", rate_limit)
    if not match:
        return 100, 60  # default: 100 per minute

    count = int(match.group(1))
    unit = match.group(2).lower()

    # Convert to seconds
    multipliers = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
        "day": 86400,
        "days": 86400,
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

        request = Request(scope)

        # Rate limit identifier (IP-based fallback).
        # We intentionally avoid JWT decoding here to keep middleware lean and robust.
        user_id = None

        identifier = user_id or request.headers.get(
            "x-forwarded-for", request.client.host if request.client else "unknown"
        )
        if "," in str(identifier):
            identifier = identifier.split(",")[0].strip()

        # Atomic check-and-increment via Lua.
        # Fail open if Redis is unavailable so core API endpoints stay reachable.
        try:
            client = _get_redis_client()
            key = f"rate_limit:{identifier}:{request.url.path}"

            # Use eval to run the script atomically
            allowed = client.eval(
                RATE_LIMIT_LUA,
                1,
                key,
                str(self.max_requests),
                str(self.window),
            )

            if not allowed:
                # Rate limit exceeded
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                )
                await response(scope, receive, send)
                return
        except Exception as exc:
            logger.warning(f"Rate limiter unavailable, allowing request: {exc}")

        await self.app(scope, receive, send)


class CSRFMiddleware:
    """CSRF protection using Double Submit Cookie pattern."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Fail-safe: frontend owns /api/auth routes.
        # If those requests hit backend, redirect them to frontend app URL when available.
        auth_path = request.url.path == "/api/auth" or request.url.path.startswith("/api/auth/")
        if auth_path:
            frontend_auth_base = (
                os.getenv("FRONTEND_URL")
                or os.getenv("NEXT_PUBLIC_APP_URL")
            )
            if frontend_auth_base:
                target = frontend_auth_base.rstrip("/")
                parsed_target = urlparse(target)
                incoming_host = request.url.netloc
                target_host = parsed_target.netloc

                # Avoid redirect loops if target and current host are identical.
                if target_host and target_host != incoming_host:
                    query = request.url.query
                    redirect_url = f"{target}{request.url.path}"
                    if query:
                        redirect_url = f"{redirect_url}?{query}"
                    response = RedirectResponse(url=redirect_url, status_code=307)
                    await response(scope, receive, send)
                    return

        # Allow test mode or explicit bypass to avoid blocking test client checks
        if os.getenv("TESTING") == "1" or os.getenv("DISABLE_CSRF") == "1":
            await self.app(scope, receive, send)
            return

        # Only check mutating methods
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Skip check for specific bypasses if needed (e.g., Stripe webhooks which use signatures)
            if request.url.path.startswith("/api/v1/billing/webhook"):
                await self.app(scope, receive, send)
                return

            # /api/auth endpoints are served by frontend Next.js route handlers.
            # If a misrouted request reaches backend, do not block it with CSRF middleware.
            if request.url.path == "/api/auth" or request.url.path.startswith("/api/auth/"):
                await self.app(scope, receive, send)
                return

            xsrf_cookie = request.cookies.get("xsrf-token")
            xsrf_header = (
                request.headers.get("x-xsrf-token")
                or request.headers.get("X-XSRF-TOKEN")
                or request.headers.get("X-Xsrf-Token")
            )

            if not xsrf_cookie or not xsrf_header or xsrf_cookie != xsrf_header:
                logger.warning(
                    f"CSRF validation failed for {request.url.path}: cookie={xsrf_cookie!r} header={xsrf_header!r}"
                )
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF validation failed. Missing or invalid XSRF token."},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


# Parse rate limit from env
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")

from contextlib import asynccontextmanager


async def reminder_worker(app: FastAPI):
    """Background task to send 15-minute reminders for upcoming events."""
    logger.info("🕒 Reminder worker started.")
    while True:
        try:
            from backend.utils.db import AsyncSessionLocal
            from backend.models.tables import EventTable, UserTable
            from backend.services.notifications import notify_event_reminder
            from sqlalchemy import select, and_
            
            if AsyncSessionLocal is None:
                await asyncio.sleep(60)
                continue
                
            now = datetime.now(timezone.utc)
            window_end = now + timedelta(minutes=16)
            
            async with AsyncSessionLocal() as db:
                stmt = select(EventTable).where(
                    and_(
                        EventTable.start_time >= now,
                        EventTable.start_time <= window_end,
                        EventTable.is_reminded == False,
                        EventTable.status == "confirmed"
                    )
                )
                result = await db.execute(stmt)
                events_to_remind = result.scalars().all()
                
                for event in events_to_remind:
                    setattr(event, "is_reminded", True)
                    await db.commit()
                    
                    user = await db.get(UserTable, event.user_id)
                    if user:
                        logger.info(f"Sending 15-min reminder for event {event.id} to user {user.id}")
                        await notify_event_reminder(
                            str(user.email),
                            [],
                            {
                                "id": event.id,
                                "user_id": event.user_id,
                                "title": event.title,
                                "start_time": event.start_time.isoformat(),
                                "end_time": event.end_time.isoformat(),
                                "user_name": user.full_name or "User",
                                "event_url": os.getenv("FRONTEND_BASE_URL", "http://localhost:3000") + "/dashboard/calendar"
                            }
                        )
        except asyncio.CancelledError:
            logger.info("Reminder worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in reminder worker: {e}")
            
        await asyncio.sleep(60)

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
            logger.error(
                f"⚠ Failed to create or verify database tables: {type(e).__name__}"
            )

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

    # 3. Auth provider auto-check removed. Using local sovereign auth.

    reminder_task = asyncio.create_task(reminder_worker(app))

    yield
    # --- Shutdown ---
    reminder_task.cancel()
    # Clean up global connections if needed


app = FastAPI(
    title="GraftAI Backend",
    description="Production API for GraftAI — AI-powered scheduling platform",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Middleware Registration ---
# ⚠️  ORDER IS CRITICAL: CORS must be outermost so that browser OPTIONS
#     preflight requests are answered BEFORE hitting the rate limiter.

# 1. CORS — Outermost layer (handles preflight OPTIONS first)
#    Collect all trusted origins from env vars + known hardcoded values.
_raw_extra = os.getenv("EXTRA_CORS_ORIGINS", "")  # comma-separated extra origins
_extra_origins = [o.strip() for o in _raw_extra.split(",") if o.strip()]

cors_origins = [
    # ── Production ──────────────────────────────────
    "https://graftai.tech",             # Primary production domain
    "https://www.graftai.tech",         # Secondary production domain
    "https://graft-ai-two.vercel.app",  # Vercel deployment preview url
    "https://graftai-api.onrender.com", # Render backend canonical domain
    # ── Configurable via Render env vars ────────────
    *([os.getenv("FRONTEND_URL")] if os.getenv("FRONTEND_URL") else []),
    *([os.getenv("LOAD_BALANCER_URL")] if os.getenv("LOAD_BALANCER_URL") else []),
    # ── Any extra origins injected at deploy time ────
    *_extra_origins,
    # ── Local development ────────────────────────────
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

class RequestIdMiddleware:
    """Attach a stable request ID to each request and response for traceability."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        scope["request_id"] = request_id
        await self.app(scope, receive, send_with_request_id)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Backend-Server", "X-Request-Id", "x-xsrf-token", "X-XSRF-TOKEN"],
    max_age=600,  # Cache preflight for 10 minutes to reduce OPTIONS overhead
)

# 2. Request ID — add trace context to all requests
app.add_middleware(RequestIdMiddleware)

# 3. Rate Limiting — Inner layer (applied only to real requests, not OPTIONS)
app.add_middleware(RateLimitMiddleware, rate_limit=_rate_limit_str)

# 3. CSRF Protection — Guarding mutations
app.add_middleware(CSRFMiddleware)

# --- Router Inclusion (API v1) ---
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(uploads_router)
v1_router.include_router(calendar_router)
v1_router.include_router(ai_router, tags=["ai"])
v1_router.include_router(proactive_router)
v1_router.include_router(analytics_router)
v1_router.include_router(consent_router)
from backend.api.admin import router as admin_router
v1_router.include_router(admin_router)
v1_router.include_router(upgrade_router)
v1_router.include_router(plugin_router)
v1_router.include_router(notifications_router)
v1_router.include_router(billing_router)

# Include v1 as both /api/v1 and flat root-level aliases
app.include_router(v1_router)
app.include_router(auth_router)

# --- Keep-Alive / Anti-Sleep Task ---
def self_pinger():
    """Background thread to keep the service awake by hitting the public URL."""
    # Wait for the server to fully stabilize
    import time
    import httpx
    time.sleep(30)
    
    # Target our own canonical URL
    public_url = os.getenv("APP_BASE_URL", "https://graftai-api.onrender.com").rstrip("/")
    health_url = f"{public_url}/health"
    
    logger.info(f"Self-pinger active. Target: {health_url}")
    while True:
        try:
            # Hitting the public URL resets Render's 15-minute idle timer
            httpx.get(health_url, timeout=10.0)
        except Exception as e:
            logger.debug(f"Self-ping failed (harmless): {e}")
        time.sleep(600) # Every 10 minutes (Render sleeps after 15)

# --- Diagnostic & Startup ---
@app.on_event("startup")
async def startup_event():
    # 1. Log all registered routes for debugging
    for route in app.routes:
        if hasattr(route, "path"):
            logger.info(f"Route: {route.path}")
    
    # 2. Start self-pinger in a daemon thread
    import threading
    threading.Thread(target=self_pinger, daemon=True).start()


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return Response(status_code=404)


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "message": "GraftAI Sovereign API is online.",
        "version": "1.0.0",
        "scaling_pool": "3 Replicas (Active)",
        "rate_limit_active": True,
    }


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "environment": "production-hardened"}


@app.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    # 1. Verify database connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness DB check failed: {e}")
        raise HTTPException(status_code=503, detail="Database not ready")

    # 2. Verify Redis connectivity
    try:
        r = _get_redis_client()
        r.ping()
    except Exception as e:
        logger.warning(f"Readiness Redis check degraded: {e}")
        # allow partial readiness for availability

    return {"status": "ready"}
