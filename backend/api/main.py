import os
import sys
import re
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

dotenv_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.auth.routes     import router as auth_router
from backend.api.calendar    import router as calendar_router
from backend.api.notifications import router as notifications_router
from backend.api.users       import router as users_router
from backend.api.uploads     import router as uploads_router
from backend.services.ai        import router as ai_router
from backend.services.analytics import router as analytics_router
from backend.services.consent   import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade   import router as upgrade_router
from backend.services.plugin_api import router as plugin_router

from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase
from backend.scripts.db_repair import repair_database


# ── Rate Limiting — in-process sliding window ─────────────────────────────────
# On Render free tier with a single dyno, in-process is cheaper than a Redis
# round-trip on every request.  Redis-backed rate limiting is preserved as
# fallback for multi-instance deployments.

import time
from collections import defaultdict, deque

_rate_buckets: dict[str, deque] = defaultdict(deque)


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
    """Sliding-window in-process rate limiter — zero Redis calls."""

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

        client_ip = request.headers.get("x-forwarded-for", "")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        key = f"{client_ip}:{request.url.path}"
        now = time.time()
        bucket = _rate_buckets[key]

        # Evict timestamps outside the window
        while bucket and bucket[0] < now - self.window:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )
            await response(scope, receive, send)
            return

        bucket.append(now)
        await self.app(scope, receive, send)


# ── Lifespan ──────────────────────────────────────────────────────────────────
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB tables
    if db_utils.engine:
        try:
            async with db_utils.engine.begin() as conn:
                await conn.run_sync(ModelsBase.metadata.create_all)
            logger.info("Database tables verified.")
            
            # Application-level schema repairs (e.g. missing columns from legacy deploys)
            await repair_database()
            
        except Exception as exc:
            logger.error(f"DB initialization/repair error: {type(exc).__name__}")

    # Password self-test
    try:
        from backend.services.auth_utils import get_password_hash, verify_password
        _pw = "StartupSelfTest99!"
        if not verify_password(_pw, get_password_hash(_pw)):
            raise RuntimeError("Password self-test failed")
        logger.info("Password hashing verified.")
    except Exception as exc:
        logger.critical(f"Password hashing failure: {exc}")
        raise

    yield
    # Shutdown: clean up rate-limit buckets to avoid memory leak on reload
    _rate_buckets.clear()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GraftAI Backend",
    description="AI-powered scheduling platform API",
    version="1.1.0",
    lifespan=lifespan,
)

# ── CORS (outermost — must answer OPTIONS before rate limiter) ────────────────
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

# ── Rate limiter (inner, skips OPTIONS already) ─────────────────────────────
_rate_limit_str = os.getenv("RATE_LIMIT", "100/minute")
app.add_middleware(RateLimitMiddleware, rate_limit=_rate_limit_str)

# ── Routers ───────────────────────────────────────────────────────────────────
from fastapi import APIRouter

v1 = APIRouter(prefix="/api/v1")

# Auth exposed at both /auth (OAuth callbacks) and /api/v1/auth
app.include_router(auth_router)
v1.include_router(auth_router)

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
v1.include_router(mfa_router)

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
