import os
import sys
import re
import logging
import asyncio
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Silencing noise: Filter out frequent health checks from console logs
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Returns True to keep the log, False to drop it
        msg = record.getMessage()
        return "GET /health" not in msg and "HEAD /health" not in msg

# Apply the filter to the uvicorn access logger if it exists
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

# Ensure project root is on sys.path so `import backend...` works even when the process starts from inside backend/
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load env FIRST so all modules can read env vars
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

from fastapi import FastAPI, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis

from backend.api import (
    calendar as calendar_module,
    users as users_module,
    uploads as uploads_module,
    notifications as notifications_module,
    zoom as zoom_module,
    integrations as integrations_module,
    organizations as organizations_module
)
from backend.services import (
    ai as ai_module,
    analytics as analytics_module,
    consent as consent_module,
    proactive as proactive_module,
    upgrade as upgrade_module,
    plugin_api as plugin_module
)
from backend.auth.routes import router as auth_router
from backend.auth.schemes import get_current_user

from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase

from backend.services.redis_client import get_redis, check_rate_limit
from backend.services.db_sync import sync_schema

# --- Configuration ---
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")

_raw_extra = os.getenv("EXTRA_CORS_ORIGINS", "")
_extra_origins = [o.strip() for o in _raw_extra.split(",") if o.strip()]

cors_origins = list(set([
    "https://graft-ai-two.vercel.app",
    "https://graftai.onrender.com",
    *([os.getenv("FRONTEND_URL")] if os.getenv("FRONTEND_URL") else []),
    *([os.getenv("FRONTEND_BASE_URL")] if os.getenv("FRONTEND_BASE_URL") else []),
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://[::1]:3000",
    "http://[::1]:3001",
    # Local Network IP wildcarding (handled by dynamic reflection in Dev)
    *_extra_origins,
]))
logger.info(f"🛡️ [CORS] Internal Allow-List: {cors_origins}")

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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple Redis-backed rate limiting middleware."""

    def __init__(self, app, rate_limit: str = "100/minute"):
        super().__init__(app)
        self.max_requests, self.window = _parse_rate_limit(rate_limit)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for OPTIONS requests (preflight) to allow CORS headers
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get client IP
        client_ip = request.headers.get(
            "x-forwarded-for", request.client.host if request.client else "unknown"
        )
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        try:
            # Atomic check-and-increment via centralized Redis service
            key = f"rate_limit:{client_ip}:{request.url.path}"
            allowed = await check_rate_limit(key, self.max_requests, self.window)

            if not allowed:
                # Rate limit exceeded
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                )
        except Exception as e:
            # Fail open if Redis is unreachable to prevent API downtime
            logger.error(f"Rate limiting error (failing open): {e}")

        return await call_next(request)


class TraceMiddleware(BaseHTTPMiddleware):
    """Deep observability middleware to trace every request to the console."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"
        origin = request.headers.get("origin", "no-origin")
        
        # Log incoming request
        logger.info(f"🔍 [REQUEST] {request.method} {request.url.path} from {client_host} (Origin: {origin})")
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(f"✅ [RESPONSE] {request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)")
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"❌ [CRASH] {request.method} {request.url.path} -> ERROR: {e} ({process_time:.2f}ms)")
            # Re-raise to let exception handlers catch it, 
            # but this trace helps see it in the terminal immediately.
            raise e


# Parse rate limit from env
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")

from contextlib import asynccontextmanager


async def reminder_worker(app: FastAPI):
    """Background task to send 15-minute reminders for upcoming events."""
    logger.info("🕒 Reminder worker waiting for system to settle...")
    await asyncio.sleep(10) # 10s cooperative delay for DB sync to finish
    logger.info("🕒 Reminder worker started.")
    while True:
        try:
            from backend.utils.db import AsyncSessionLocal
            from backend.models.tables import EventTable, UserTable
            from backend.services.notifications import notify_event_reminder
            from backend.services.redis_client import acquire_lock
            from sqlalchemy import select, and_
            
            if AsyncSessionLocal is None:
                await asyncio.sleep(60)
                continue
                
            now = datetime.now(timezone.utc)
            # Create a unique lock key for this specific minute to prevent multi-instance race conditions
            lock_key = f"reminder_worker_tick_{now.strftime('%Y%m%d_%H%M')}"
            
            if not await acquire_lock(lock_key, expiry=55):
                # Another instance is already handling this minute
                await asyncio.sleep(30)
                continue

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
                    event.is_reminded = True
                    await db.commit()
                    
                    user = await db.get(UserTable, event.user_id)
                    if user:
                        logger.info(f"Sending 15-min reminder for event {event.id} to user {user.id}")
                        await notify_event_reminder(
                            user.email,
                            [],
                            {
                                "id": event.id,
                                "user_id": event.user_id,
                                "title": event.title,
                                "category": event.category,
                                "is_meeting": event.is_meeting,
                                "meeting_link": event.meeting_link,
                                "meeting_platform": event.meeting_platform,
                                "agenda": event.agenda,
                                "attendees": event.attendees,
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

from backend.services.db_sync import sync_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure Database Schema is synced and background workers start
    try:
        from sqlalchemy import text
        # Fast Database Sanity Check
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Database connectivity verified")
        
        await sync_schema()
        logger.info("✅ Database schema synchronized")
    except Exception as e:
        logger.error(f"❌ Database synchronization failed: {e}")
        
    # Start background workers
    reminder_task = asyncio.create_task(reminder_worker(app))
    
    yield
    
    # Shutdown: Cleanup
    reminder_task.cancel()
    try:
        await reminder_task
    except asyncio.CancelledError:
        pass

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


app = FastAPI(
    title="GraftAI Backend",
    description="Production API for GraftAI — AI-powered scheduling platform",
    version="1.0.0",
    lifespan=lifespan,
)


# 0. Request Tracing — Absolute Outermost (First in, last out)
app.add_middleware(TraceMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that ensures CORS headers are attached 
    even on internal server errors (critical for frontend visibility).
    """
    tbl = traceback.format_exc()
    logger.error(f"🌊 [GLOBAL ERROR] {request.method} {request.url.path}\n{tbl}")
    
    # Get origin for reflection
    origin = request.headers.get("origin")
    
    # Check if origin is allowed or if it's a local network IP in Dev
    is_allowed = origin in cors_origins if origin else False
    if not is_allowed and origin and (origin.startswith("http://192.168.") or origin.startswith("http://10.") or origin.startswith("http://172.")):
        is_allowed = True # Auto-allow local network in Dev
    
    headers = {}
    if is_allowed:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please check backend logs.",
            "error_type": type(exc).__name__,
            "message": str(exc)
        },
        headers=headers
    )

# 3. CORS — Final wrapper for credentials and preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"], 
    expose_headers=["X-Backend-Version", "X-Request-Id"],
    max_age=600,
)
# Ensure allow_private_network is supported and X-Backend-Version is set
if hasattr(app.user_middleware[-1], 'cls') and app.user_middleware[-1].cls == CORSMiddleware:
    app.user_middleware[-1].options['allow_private_network'] = True

# --- Router Inclusion (API v1) ---
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(organizations_module.router)
v1_router.include_router(users_module.router)
v1_router.include_router(uploads_module.router)
v1_router.include_router(calendar_module.router)
v1_router.include_router(ai_module.router, tags=["ai"])
v1_router.include_router(proactive_module.router)
v1_router.include_router(analytics_module.router)
v1_router.include_router(consent_module.router)
v1_router.include_router(upgrade_module.router)
v1_router.include_router(plugin_module.router)
v1_router.include_router(notifications_module.router)
v1_router.include_router(zoom_module.router)
v1_router.include_router(integrations_module.router)

@v1_router.get("/health")
def v1_health():
    """Versioned health check for frontend use."""
    return health()


app.include_router(v1_router)


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
        "version": "1.0.0",
        "scaling_pool": "3 Replicas (Active)",
        "rate_limit_active": True,
    }


@app.get("/health")
def health():
    """Robust health check that reports on AI service status."""
    try:
        from backend.services import langchain_client
        
        # Check if llm is the real one or the dummy
        llm_instance = langchain_client.get_llm()
        llm_type = type(llm_instance).__name__
        is_dummy = "Dummy" in llm_type
        
        return {
            "status": "ok", 
            "environment": os.getenv("ENV", "development"),
            "ai": {
                "llm_type": llm_type,
                "configured": not is_dummy,
                "groq_ready": langchain_client._llm is not None,
                "openai_ready": os.getenv("OPENAI_API_KEY") is not None,
                "vector_store_ready": langchain_client._vector_store is not None
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
