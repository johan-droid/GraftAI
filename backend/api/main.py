import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import httpx
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.utils.error_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.utils.logger import configure_logging

configure_logging()
for dotenv_path in [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local", PROJECT_ROOT / ".env.development", PROJECT_ROOT / ".env.development.local", PROJECT_ROOT / "backend" / ".env", PROJECT_ROOT / "backend" / ".env.local", PROJECT_ROOT / "backend" / ".env.development", PROJECT_ROOT / "backend" / ".env.development.local"]:
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)
load_dotenv()
from backend.ai.agents.base import AgentTimeoutError
from backend.services.migrations import run_migrations
from backend.utils import db as db_utils


def _parse_comma_separated_env(name: str, default: str="") -> list[str]:
    raw = os.getenv(name, default)
    return [value.strip() for value in raw.split(",") if value.strip()]

def _extract_hostname(url: str | None) -> str | None:
    if not url:
        return None
    return url.split("//", 1)[-1].split("/", 1)[0]

def _normalize_origin(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"

def _validate_production_env() -> None:
    env = os.getenv("ENV", "development").lower()
    if env != "production":
        return
    required_vars = ["SECRET_KEY", "DATABASE_URL", "FRONTEND_URL", "NEXT_PUBLIC_API_URL", "REDIS_URL"]
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing required production environment variables: " + ", ".join(missing))
    if os.getenv("SECRET_KEY") in {"super-secret-college-project-key-change-in-prod", "your-super-secret-key-change-in-production", ""}:
        msg = "CRITICAL: SECRET_KEY must be changed in production."
        raise RuntimeError(msg)

def _init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    from sentry_sdk.integrations.celery import CeleryIntegration
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENV", "development")),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        integrations=[CeleryIntegration()],
    )
_validate_production_env()
_init_sentry()

async def _self_ping_loop(port: str, interval_seconds: int=240) -> None:
    url = f"http://127.0.0.1:{port}/health"
    async with httpx.AsyncClient() as client:
        while True:
            with suppress(Exception):
                await client.get(url, timeout=10.0)
            await asyncio.sleep(interval_seconds)

@asynccontextmanager
async def lifespan(app: FastAPI):
    skip_migrations = os.getenv("SKIP_DB_MIGRATIONS", "false").strip().lower() in {"1", "true", "yes"}
    if skip_migrations:
        logging.info("[STARTUP] SKIP_DB_MIGRATIONS=true — skipping database migrations")
    elif not db_utils.DATABASE_URL:
        logging.warning("[STARTUP] DATABASE_URL not set — skipping database migrations. Database features will be disabled.")
    else:
        run_migrations()
    try:
        from backend.services.dlq_handlers import register_dlq_handlers
        handler_count = register_dlq_handlers()
        logging.info(f"[STARTUP] Registered {handler_count} DLQ handlers")
    except Exception as e:
        logging.exception(f"[STARTUP] Failed to register DLQ handlers: {e}")
    port = os.getenv("PORT", "8000")
    ping_enabled = os.getenv("SELF_PING_ENABLED", "true").lower() not in {"0", "false", "no"}
    ping_task = None
    if ping_enabled:
        ping_interval = int(os.getenv("SELF_PING_INTERVAL_SECONDS", "30"))
        ping_task = asyncio.create_task(_self_ping_loop(port, ping_interval))
        app.state.self_ping_task = ping_task
    # Periodic refresh of API key prefix index (keeps in-memory cache fresh)
    api_key_refresh_task = None
    try:
        refresh_seconds = int(os.getenv("API_KEY_PREFIX_REFRESH_SECONDS", "300"))
    except Exception:
        refresh_seconds = 300

    async def _refresh_prefix_index_loop():
        from backend.utils.rate_limiter import get_rate_limiter
        from backend.utils.db import get_db_context
        from sqlalchemy import text
        limiter = get_rate_limiter(redis_url=os.getenv("REDIS_URL", None))
        while True:
            try:
                if db_utils.DATABASE_URL:
                    async with get_db_context() as session:
                        rows = await session.execute(text("SELECT ak.key_prefix, ak.key_hash, u.tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.is_active = true"))
                        # rebuild index atomically
                        new_index: dict = {}
                        for key_prefix, key_hash, tier in rows:
                            new_index.setdefault(key_prefix, []).append((key_hash, tier))
                        limiter.api_key_prefix_index = new_index
                        limiter.api_key_tiers = {k: v for k, v in limiter.api_key_tiers.items() if k in limiter.api_key_tiers}
            except Exception:
                logger.exception("Failed to refresh API key prefix index")
            await asyncio.sleep(refresh_seconds)

    api_key_refresh_task = asyncio.create_task(_refresh_prefix_index_loop())
    app.state.api_key_refresh_task = api_key_refresh_task
    try:
        from backend.utils.ai_cost_guard import implement_ai_cost_controls
        from backend.utils.cache_optimizer import initialize_cache_optimizer
        from backend.utils.cost_optimizer import implement_cost_controls
        from backend.utils.database_optimizer import initialize_database_optimizer
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            await initialize_database_optimizer(database_url)
        await implement_cost_controls()
        await implement_ai_cost_controls()
        await initialize_cache_optimizer()
        logger.info("Cost optimization systems initialized")
        if db_utils.DATABASE_URL:
            from backend.utils.rate_limiter import get_rate_limiter
            from backend.utils.db import get_db_context
            from sqlalchemy import text
            limiter = get_rate_limiter(redis_url=os.getenv("REDIS_URL", None))
            async with get_db_context() as session:
                rows = await session.execute(text("SELECT ak.key_prefix, ak.key_hash, u.tier FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.is_active = true"))
                for key_prefix, key_hash, tier in rows:
                    limiter.api_key_prefix_index.setdefault(key_prefix, []).append((key_hash, tier))
            logger.info("Rate limiter API key prefix index populated")
    except Exception as e:
        logger.exception("Failed to initialize cost optimizations: %s", e)
    yield
    if ping_task:
        ping_task.cancel()
        with suppress(asyncio.CancelledError):
            await ping_task
    if api_key_refresh_task:
        api_key_refresh_task.cancel()
        with suppress(asyncio.CancelledError):
            await api_key_refresh_task
    try:
        from backend.core.redis import close_redis
        await close_redis()
    except Exception:
        logger.exception("Failed to close Redis connection during shutdown")
    if hasattr(db_utils, "engine"):
        await db_utils.engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(title="GraftAI Monolith", description="A bare-minimum, high-performance monolithic backend for GraftAI.", version="2.0.0", lifespan=lifespan)
    if os.getenv("SENTRY_DSN"):
        app.add_middleware(SentryAsgiMiddleware)
    env = os.getenv("ENV", "development").lower()
    frontend_candidates = _parse_comma_separated_env("FRONTEND_URL") or _parse_comma_separated_env("FRONTEND_BASE_URL")
    if not frontend_candidates:
        frontend_candidates = ["http://localhost:3000", "http://127.0.0.1:3000"]
    extra_cors_origins = _parse_comma_separated_env("EXTRA_CORS_ORIGINS")
    allow_origins = [origin for origin in (_normalize_origin(value) for value in [*frontend_candidates, *extra_cors_origins]) if origin]
    allow_origins = list(dict.fromkeys(allow_origins))
    if env == "production":
        if "https://www.graftai.tech" in allow_origins and "https://graftai.tech" not in allow_origins:
            allow_origins.append("https://graftai.tech")
        if "https://graftai.tech" in allow_origins and "https://www.graftai.tech" not in allow_origins:
            allow_origins.append("https://www.graftai.tech")
        https_allow_origins = [origin for origin in allow_origins if origin.startswith("https://")]
        if https_allow_origins:
            allow_origins = https_allow_origins
    trusted_hosts = [host for host in (_extract_hostname(value) for value in _parse_comma_separated_env("TRUSTED_HOSTS")) if host]
    if not trusted_hosts:
        if env == "production":
            trusted_hosts = [_extract_hostname(host) for host in allow_origins if host]
            backend_host = _extract_hostname(os.getenv("BACKEND_URL") or os.getenv("APP_BASE_URL"))
            if backend_host:
                trusted_hosts.append(backend_host)
            if os.getenv("RENDER") is not None:
                trusted_hosts.append("*.onrender.com")
            if os.getenv("VERCEL") is not None:
                trusted_hosts.append("*.vercel.app")
            trusted_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0", "graftai.tech", "www.graftai.tech"])
            trusted_hosts = [host for host in dict.fromkeys(trusted_hosts) if host]
        else:
            trusted_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "graftai.tech", "*.vercel.app", "*.onrender.com"]
    trusted_proxy_env = os.getenv("TRUSTED_PROXY_IPS", "")
    trusted_proxy_ips = [ip.strip() for ip in trusted_proxy_env.split(",") if ip.strip()]
    if trusted_proxy_ips:
        try:
            import importlib
            proxy_module = importlib.import_module("starlette.middleware.proxy_headers")
            ProxyHeadersMiddleware = proxy_module.ProxyHeadersMiddleware
            app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=trusted_proxy_ips)
        except Exception as e:
            logging.warning("Failed to add ProxyHeadersMiddleware: %s", e)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    from starlette.middleware.base import BaseHTTPMiddleware

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        """Add security headers to all responses."""

        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            request_path = request.url.path
            is_docs_request = request_path in {"/docs", "/redoc", "/openapi.json"} or request_path.startswith("/docs/")
            if is_docs_request:
                response.headers["Content-Security-Policy"] = "default-src 'self' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self'; frame-ancestors 'none';"
            else:
                response.headers["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'; img-src 'self' data:; style-src 'self'; font-src 'self'; connect-src 'self';"
            response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
            return response
    app.add_middleware(SecurityHeadersMiddleware)

    class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
        """Reject requests with bodies larger than the configured byte limit."""

        def __init__(self, app, max_body_size: int=2 * 1024 * 1024):
            super().__init__(app)
            self.max_body_size = max_body_size

        async def dispatch(self, request, call_next):
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    if int(content_length) > self.max_body_size:
                        return JSONResponse({"detail": "Request body too large."}, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                except ValueError:
                    pass
            else:
                # No Content-Length header (chunked encoding) — enforce via streaming
                original_receive = request.receive

                async def limited_receive():
                    total = 0
                    while True:
                        msg = await original_receive()
                        if msg["type"] == "http.disconnect":
                            return msg
                        if msg["type"] == "http.request":
                            chunk = msg.get("body", b"")
                            total += len(chunk)
                            if total > self.max_body_size:
                                raise HTTPException(status_code=413, detail="Request body too large.")
                            if not msg.get("more_body", False):
                                return msg
                            return msg
                        return msg

                request._receive = limited_receive
            return await call_next(request)
    app.add_middleware(LimitUploadSizeMiddleware)
    from backend.utils.security_middleware import (
        InputValidationMiddleware,
        RequestLoggingMiddleware,
    )
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    import uuid

    from starlette.middleware.base import BaseHTTPMiddleware

    class RequestIDMiddleware(BaseHTTPMiddleware):
        """Add X-Request-ID header for request correlation across services."""

        async def dispatch(self, request, call_next):
            request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            request.state.request_id = request_id
            if hasattr(request.state, "logger_extra"):
                request.state.logger_extra["request_id"] = request_id
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
    app.add_middleware(RequestIDMiddleware)
    from backend.utils.rate_limiter import RateLimitMiddleware
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url, default_limit=100, default_window=60, strategy="sliding_window", skip_paths=["/health", "/", "/docs", "/redoc", "/openapi.json", "/metrics"])
    from backend.utils.cost_optimizer import CostMonitoringMiddleware
    app.add_middleware(CostMonitoringMiddleware)
    allow_origin_regex = "^https?://(?:localhost|127\\.0\\.0\\.1)(?::\\d+)?$" if env != "production" else None
    app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_origin_regex=allow_origin_regex, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["x-xsrf-token", "Location"])

    async def agent_timeout_handler(request: "Request", exc: Exception) -> "JSONResponse":
        if not isinstance(exc, AgentTimeoutError):
            raise exc
        return JSONResponse(status_code=504, content={"error": "AI operation timed out.", "code": "agent_timeout", "detail": str(exc)})
    app.add_exception_handler(AgentTimeoutError, agent_timeout_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    from backend.api.advanced_analytics_routes import (
        router as advanced_analytics_router,
    )
    from backend.api.ai_chat import router as ai_chat_router
    from backend.api.analytics import router as analytics_router
    from backend.api.automation_routes import router as automation_router
    from backend.api.billing import router as billing_router
    from backend.api.booking_automation import router as booking_automation_router
    from backend.api.bookings import router as bookings_router
    from backend.api.calendar import router as calendar_router
    from backend.api.email_template_routes import router as email_template_router
    from backend.api.event_types import router as event_types_router
    from backend.api.integration_routes import router as integration_router
    from backend.api.monitoring import router as monitoring_router
    from backend.api.notifications import router as notifications_router
    from backend.api.plugins import router as plugins_router
    from backend.api.proactive import router as proactive_router
    from backend.api.public import router as public_router
    from backend.api.resource_routes import router as resource_router
    from backend.api.team_routes import router as team_router
    from backend.api.users import router as users_router
    from backend.api.v1.audit import router as audit_router
    from backend.api.video_conference_routes import router as video_conference_router
    from backend.api.webhooks import router as webhooks_router
    from backend.api.workflows import router as workflows_router
    from backend.auth.routes import router as auth_router
    from backend.routes.calendar_routes import router as calendar_integration_router
    from backend.routes.gdpr_routes import router as gdpr_router
    from backend.services.ai import router as ai_router
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(bookings_router, prefix="/api/v1")
    app.include_router(booking_automation_router, prefix="/api/v1")
    from backend.api.auth import router as session_auth_router
    app.include_router(session_auth_router, prefix="/api/v1/auth")
    app.include_router(calendar_integration_router)
    app.include_router(gdpr_router)
    app.include_router(team_router, prefix="/api/v1")
    app.include_router(workflows_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(integration_router, prefix="/api/v1")
    app.include_router(email_template_router, prefix="/api/v1")
    app.include_router(video_conference_router, prefix="/api/v1")
    app.include_router(resource_router, prefix="/api/v1")
    app.include_router(advanced_analytics_router, prefix="/api/v1")
    app.include_router(automation_router, prefix="/api/v1")
    app.include_router(calendar_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    app.include_router(proactive_router, prefix="/api/v1")
    app.include_router(event_types_router, prefix="/api/v1")
    app.include_router(plugins_router, prefix="/api/v1")
    app.include_router(webhooks_router, prefix="/api/v1")
    # Public routes are versioned under /api/v1 for consistency
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(ai_chat_router, prefix="/api/v1")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")
    app.include_router(monitoring_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1/audit")

    @app.get("/health")
    async def health_check(request: Request):
        from backend.core.redis import get_redis
        from backend.utils.db import AsyncSessionLocal
        from sqlalchemy import text

        checks = {"database": {"status": "unknown"}, "redis": {"status": "unknown"}}
        overall = "healthy"

        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            checks["database"] = {"status": "healthy"}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "error": str(e)}
            overall = "unhealthy"

        try:
            r = await get_redis()
            if r:
                await r.ping()
                checks["redis"] = {"status": "healthy"}
            else:
                checks["redis"] = {"status": "degraded", "detail": "in-memory fallback"}
        except Exception as e:
            checks["redis"] = {"status": "unhealthy", "error": str(e)}
            overall = "unhealthy"

        return {"status": overall, "checks": checks, "request_id": getattr(request.state, "request_id", None)}

    @app.api_route("/", methods=["GET", "HEAD"])
    async def root():
        return {"app": "GraftAI", "status": "running", "frontend_url": os.getenv("FRONTEND_URL", os.getenv("FRONTEND_BASE_URL", "http://localhost:3000"))}
    # Backwards-compatible redirects: /api/* -> /api/v1/*
    from fastapi.responses import RedirectResponse

    @app.get("/api", include_in_schema=False)
    async def _redirect_api_root():
        return RedirectResponse(url="/api/v1", status_code=308)

    @app.get("/api/{full_path:path}", include_in_schema=False)
    async def _redirect_api(full_path: str, request: Request):
        target = f"/api/v1/{full_path}"
        return RedirectResponse(url=target, status_code=308)
    return app
app = create_app()
