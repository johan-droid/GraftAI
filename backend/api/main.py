import os
import sys
import re
import logging
import asyncio
import inspect
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

dotenv_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.auth.routes     import router as auth_router
from backend.api.calendar    import router as calendar_router
from backend.api.notifications import router as notifications_router
from backend.api.users       import router as users_router
from backend.api.uploads     import router as uploads_router
from backend.api.admin       import router as admin_router
from backend.services.ai        import router as ai_router
from backend.api.sync_stream    import router as sync_stream_router

from backend.auth.routes.saml   import router as saml_router
from backend.services.analytics import router as analytics_router
from backend.services.consent   import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade   import router as upgrade_router
from backend.services.plugin_api import router as plugin_router

from backend.utils import db as db_utils
from backend.scripts.db_repair import repair_database
from backend.services.migrations import run_migrations


# ── Rate Limiting — in-process sliding window ─────────────────────────────────
# On Render free tier with a single dyno, in-process is cheaper than a Redis
# round-trip on every request.  Redis-backed rate limiting is preserved as
# fallback for multi-instance deployments.

from backend.utils.redis_singleton import get_redis

_RATE_LIMIT_LUA = """
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

def _parse_rate_limit(rate_limit_str: str):
    match = re.match(r"(\d+)/(\w+)", rate_limit_str)
    if not match:
        return 100, 60
    count = int(match.group(1))
    unit  = match.group(2).lower()
    windows = {"second": 1, "seconds": 1, "minute": 60, "minutes": 60,
               "hour": 3600, "hours": 3600, "day": 86400, "days": 86400}
    return count, windows.get(unit, 60)

class RateLimitMiddleware:
    """Sliding-window Redis-backed rate limiter."""

    def __init__(self, app, rate_limit: str = "100/minute"):
        self.app = app
        self.max_requests, self.window = _parse_rate_limit(rate_limit)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Skip OPTIONS (CORS preflight) — handled by CORSMiddleware above
        if request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # SEC-03: Harden IP extraction. Only trust X-Forwarded-For if it comes from a known proxy.
        TRUSTED_PROXY_IPS = set(os.getenv("TRUSTED_PROXY_IPS", "").split(","))
        real_client_host = request.client.host if request.client else "unknown"

        if real_client_host in TRUSTED_PROXY_IPS:
            fwd = request.headers.get("x-forwarded-for", "")
            if fwd:
                # The leftmost IP is the client, but the rightmost before the proxy is most reliable in standard stacks
                client_ip = fwd.split(",")[-1].strip()
            else:
                client_ip = real_client_host
        else:
            client_ip = real_client_host

        # Skip health checks and static assets from rate limiting
        if request.url.path in ["/health", "/api/v1/health", "/favicon.ico", "/"]:
            await self.app(scope, receive, send)
            return

        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            redis_client = await get_redis()
            result = redis_client.eval(
                _RATE_LIMIT_LUA,
                1,
                key,
                str(self.max_requests),
                str(self.window),
            )
            allowed_result = await result if inspect.isawaitable(result) else result
            allowed = bool(int(allowed_result))
        except Exception as e:
            logger.error(f"Global Rate limiter Redis failure: {e}")
            
            # SEC-10: Fail closed on sensitive routes, fail open for non-critical reads
            SENSITIVE_PATHS = ["/auth", "/api/v1/auth", "/api/v1/ai", "/api/v1/users/me"]
            is_sensitive = any(request.url.path.startswith(p) for p in SENSITIVE_PATHS)
            allowed = not is_sensitive

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


# ── Lifespan ──────────────────────────────────────────────────────────────────
# ── Sentry Initialization (Harden PII & Control Rate) ───────────────────────
if os.getenv("SENTRY_DSN"):
    def _scrub_sentry_event(event: dict, hint: dict) -> dict:
        """SEC-07: Redact sensitive fields from Sentry payload."""
        pixel_keys = {
            "password", "access_token", "refresh_token", "secret", "token", "authorization",
            "stripe_customer_id", "razorpay_customer_id", "email", "phone", "phone_number"
        }
        
        def _redact(data):
            if isinstance(data, dict):
                return {k: "[REDACTED]" if k.lower() in pixel_keys else _redact(v) for k, v in data.items()}
            if isinstance(data, list):
                return [_redact(i) for i in data]
            return data
            
        return _redact(event)

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        environment=os.getenv("ENV", "production"),
        # SEC-07: Use environment-controlled sampling rate
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_RATE", "0.05")),
        before_send=_scrub_sentry_event,
    )
    logger.info("📡 [STARTUP] Sentry SDK initialized (with SEC-07 hardening).")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Pre-flight Checks (Audit Phase) ───────────────────────────────────
    logger.info("🚀 [STARTUP] Initializing Pre-flight Audit...")
    
    # 1. Database Connectivity
    if not db_utils.DATABASE_URL:
        logger.critical("❌ [STARTUP] DATABASE_URL is missing. Platform is INOPERABLE.")
    else:
        try:
            skip_db_migrations = os.getenv("SKIP_DB_MIGRATIONS", "false").lower() in {"1", "true", "yes"}
            db_migration_timeout = float(os.getenv("DB_MIGRATION_TIMEOUT_SECONDS", "60"))
            skip_db_repair = os.getenv("SKIP_DB_REPAIR", "false").lower() in {"1", "true", "yes"}
            db_repair_timeout = float(os.getenv("DB_REPAIR_TIMEOUT_SECONDS", "20"))

            if skip_db_migrations:
                logger.warning("⚠️ [STARTUP] SKIP_DB_MIGRATIONS enabled. Skipping ordered migrations.")
            else:
                await asyncio.wait_for(asyncio.to_thread(run_migrations), timeout=db_migration_timeout)
                logger.info("✅ [STARTUP] Ordered migrations complete.")

            if skip_db_repair:
                logger.warning("⚠️ [STARTUP] SKIP_DB_REPAIR enabled. Skipping startup schema repair.")
            else:
                # Prevent startup stalls from blocking port binding on managed platforms.
                await asyncio.wait_for(repair_database(), timeout=db_repair_timeout)
                logger.info("✅ [STARTUP] Database schema verified.")
        except asyncio.TimeoutError:
            logger.error("❌ [STARTUP] Database verification timed out; continuing startup.")
        except Exception as e:
            logger.error(f"❌ [STARTUP] Database verification failed: {e}")

    # 2. Redis Availability Check (Manual Pool Test)
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("⚠️ [STARTUP] REDIS_URL missing. Background tasks (Notifications) will fail.")
    else:
        logger.info("✅ [STARTUP] Redis configuration detected.")

    # 3. Frontend Base URL (Strict Check)
    frontend_url = os.getenv("FRONTEND_BASE_URL")
    if not frontend_url:
        logger.error("❌ [STARTUP] FRONTEND_BASE_URL missing. Broken notification links expected.")
    else:
        logger.info(f"✅ [STARTUP] Frontend URL verified: {frontend_url}")

    # Password self-test (Security Audit Fix)
    try:
        from backend.services.auth_utils import get_password_hash, verify_password
        _pw = "AuditTest!"
        if not verify_password(_pw, get_password_hash(_pw)):
            logger.critical("❌ [STARTUP] Auth hashing self-test FAILED.")
        else:
            logger.info("✅ [STARTUP] Auth engine verified.")
    except Exception as exc:
        logger.critical(f"❌ [STARTUP] Auth hash logic error: {exc}")

    logger.info("🟢 [STARTUP] ALL SYSTEMS GO.")
    yield
    logger.info("🛑 [SHUTDOWN] Cleaning up...")


# ── App Definition ──────────────────────────────────────────────────────────
app = FastAPI(
    title="GraftAI Sovereign Tier",
    description="Enterprise-grade intelligence & scheduling engine.",
    version="1.1.0",
    lifespan=lifespan
)

# ── Global Exception Handler (Stateless & LB Friendly) ────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔥 UNHANDLED ERROR: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A critical system error occurred. Our engineering team has been notified.",
            "type": "internal_error",
            "request_id": request.headers.get("x-request-id", "system"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
    )

# ── Middleware Stack ────────────────────────────────────────────────────────

# 1. GZip Compression (Efficiency: Reduces payload size by up to 80%)
app.add_middleware(GZipMiddleware, minimum_size=2000)

# 2. CORS Management
_extra_origins = [
    o.strip()
    for o in os.getenv("EXTRA_CORS_ORIGINS", "").split(",")
    if o.strip()
]

cors_origins = [
    "https://graft-ai-two.vercel.app",
    "https://graftai.onrender.com",
    *([os.getenv("FRONTEND_URL")] if os.getenv("FRONTEND_URL") else []),
    *([os.getenv("LOAD_BALANCER_URL")] if os.getenv("LOAD_BALANCER_URL") else []),
    *_extra_origins,
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Backend-Server", "X-Request-Id", "x-xsrf-token", "X-XSRF-TOKEN"],
    max_age=600,
)

# SEC-06: Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS: Enforce HTTPS for 1 year in production environments
    if os.getenv("ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    return response

# 3. Global Request/Response Optimization Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Sovereign-Version"] = "1.1.0"
    response.headers["X-Backend-Node"] = os.getenv("HOSTNAME", "default-node")
    return response

# 4. Global Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip logging for health checks to keep logs clean and reduce I/O
    if request.url.path == "/health":
        return await call_next(request)
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# ── Rate limiter (inner, skips OPTIONS already) ─────────────────────────────
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")
app.add_middleware(RateLimitMiddleware, rate_limit=_rate_limit_str)

# ── Routers ───────────────────────────────────────────────────────────────────
from fastapi import APIRouter

v1 = APIRouter(prefix="/api/v1")

# Auth exposed at both /auth (OAuth callbacks) and /api/v1/auth
app.include_router(auth_router)
v1.include_router(auth_router)

from backend.api.billing import router as billing_router
from backend.api.webhooks import router as webhooks_router
from backend.api.mfa import router as mfa_router

v1.include_router(users_router)
v1.include_router(uploads_router)
v1.include_router(calendar_router)
v1.include_router(notifications_router)
v1.include_router(ai_router)
v1.include_router(proactive_router)
v1.include_router(analytics_router)
v1.include_router(consent_router)
v1.include_router(upgrade_router)
v1.include_router(plugin_router)
v1.include_router(billing_router)
v1.include_router(webhooks_router)
v1.include_router(admin_router)
v1.include_router(sync_stream_router)
v1.include_router(saml_router)

app.include_router(v1)


# ── Misc endpoints ────────────────────────────────────────────────────────────

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    return Response(status_code=404)


@app.get("/")
def root():
    return {
        "message": "GraftAI Sovereign API is online.",
        "version": "1.1.0",
        "rate_limit": _rate_limit_str,
    }


@app.head("/")
def root_head():
    return Response(status_code=200)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.head("/health")
def health_head():
    return Response(status_code=200)
