import asyncio
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import httpx
import sentry_sdk
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

# Ensure absolute imports like `backend.*` resolve even when launched from `backend/`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils import db as db_utils
from backend.utils.error_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.utils.logger import configure_logging
from backend.services.migrations import run_migrations

configure_logging()

# Load environment variables
load_dotenv()


def _parse_comma_separated_env(name: str, default: str = "") -> list[str]:
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

    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "FRONTEND_URL",
        "NEXT_PUBLIC_API_URL",
        "REDIS_URL",
    ]

    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required production environment variables: " + ", ".join(missing)
        )

    if os.getenv("SECRET_KEY") in {"super-secret-college-project-key-change-in-prod", "your-super-secret-key-change-in-production", ""}:
        raise RuntimeError("CRITICAL: SECRET_KEY must be changed in production.")


def _init_sentry() -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENV", "development")),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    )


_validate_production_env()
_init_sentry()

async def _self_ping_loop(port: str, interval_seconds: int = 240) -> None:
    url = f"http://127.0.0.1:{port}/health"
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(url, timeout=10.0)
            except Exception:
                pass
            await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (creates tables if they don't exist in monolith mode)
    run_migrations()
    # Inline schema mutations were removed in favor of Alembic-managed migrations
    # to avoid blocking the main event loop during startup.

    port = os.getenv("PORT", "8000")
    ping_enabled = os.getenv("SELF_PING_ENABLED", "true").lower() not in {"0", "false", "no"}
    ping_task = None
    if ping_enabled:
        ping_interval = int(os.getenv("SELF_PING_INTERVAL_SECONDS", "30"))
        ping_task = asyncio.create_task(_self_ping_loop(port, ping_interval))
        app.state.self_ping_task = ping_task

    yield

    if ping_task:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass

    # Cleanup logic (if any)
    if hasattr(db_utils, "engine"):
        await db_utils.engine.dispose()

# NOTE: _ensure_event_column_migrations removed. Schema should be managed by Alembic
# and applied before application startup (e.g., as part of container init or CI/CD).

def create_app() -> FastAPI:
    app = FastAPI(
        title="GraftAI Monolith",
        description="A bare-minimum, high-performance monolithic backend for GraftAI.",
        version="2.0.0",
        lifespan=lifespan
    )

    if os.getenv("SENTRY_DSN"):
        app.add_middleware(SentryAsgiMiddleware)

    # Trusted Host and CORS hardening
    env = os.getenv("ENV", "development").lower()
    frontend_candidates = _parse_comma_separated_env("FRONTEND_URL") or _parse_comma_separated_env("FRONTEND_BASE_URL")
    if not frontend_candidates:
        frontend_candidates = ["http://localhost:3000", "http://127.0.0.1:3000"]

    extra_cors_origins = _parse_comma_separated_env("EXTRA_CORS_ORIGINS")
    allow_origins = [
        origin
        for origin in (
            _normalize_origin(value)
            for value in [*frontend_candidates, *extra_cors_origins]
        )
        if origin
    ]
    allow_origins = list(dict.fromkeys(allow_origins))

    if env == "production":
        # Ensure both root and www variants are allowed in production CORS if either is configured.
        if "https://www.graftai.tech" in allow_origins and "https://graftai.tech" not in allow_origins:
            allow_origins.append("https://graftai.tech")
        if "https://graftai.tech" in allow_origins and "https://www.graftai.tech" not in allow_origins:
            allow_origins.append("https://www.graftai.tech")

        https_allow_origins = [origin for origin in allow_origins if origin.startswith("https://")]
        if https_allow_origins:
            allow_origins = https_allow_origins

    trusted_hosts = [
        host
        for host in (
            _extract_hostname(value)
            for value in _parse_comma_separated_env("TRUSTED_HOSTS")
        )
        if host
    ]
    if not trusted_hosts:
        if env == "production":
            trusted_hosts = [
                _extract_hostname(host)
                for host in allow_origins
                if host
            ]
            backend_host = _extract_hostname(os.getenv("BACKEND_URL") or os.getenv("APP_BASE_URL"))
            if backend_host:
                trusted_hosts.append(backend_host)

            # Always allow internal health checks and local probes in production.
            trusted_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0"])
            trusted_hosts = [host for host in dict.fromkeys(trusted_hosts) if host]
        else:
            trusted_hosts = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "*.graftai.tech",
                "*.vercel.app",
                "*.render.com",
            ]

    # If the application is behind a trusted load balancer/proxy, ensure
    # that proxy headers (X-Forwarded-For, X-Forwarded-Proto) are only
    # trusted from configured proxy IPs. TRUSTED_PROXY_IPS should be a
    # comma-separated list (e.g. "127.0.0.1,load_balancer").
    trusted_proxy_env = os.getenv("TRUSTED_PROXY_IPS", "")
    trusted_proxy_ips = [ip.strip() for ip in trusted_proxy_env.split(",") if ip.strip()]
    if trusted_proxy_ips:
        try:
            import importlib

            proxy_module = importlib.import_module("starlette.middleware.proxy_headers")
            ProxyHeadersMiddleware = getattr(proxy_module, "ProxyHeadersMiddleware")

            # Add ProxyHeadersMiddleware so downstream frameworks (Starlette/FastAPI)
            # will populate client/host values from X-Forwarded-* only when the
            # request originated from a trusted proxy.
            app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=trusted_proxy_ips)
        except Exception as e:
            logging.warning("Failed to add ProxyHeadersMiddleware: %s", e)

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Security Headers Middleware
    from starlette.middleware.base import BaseHTTPMiddleware

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        """Add security headers to all responses."""
        
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # XSS protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # HTTPS enforcement (1 year)
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Content Security Policy
            request_path = request.url.path
            is_docs_request = request_path in {"/docs", "/redoc", "/openapi.json"} or request_path.startswith("/docs/")

            if is_docs_request:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self' https://cdn.jsdelivr.net; "
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' https://cdn.jsdelivr.net; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none';"
                )
            else:
                response.headers["Content-Security-Policy"] = (
                    "default-src 'none'; "
                    "base-uri 'none'; "
                    "form-action 'none'; "
                    "frame-ancestors 'none'; "
                    "object-src 'none'; "
                    "img-src 'self' data:; "
                    "style-src 'self'; "
                    "font-src 'self'; "
                    "connect-src 'self';"
                )
            
            # Permissions Policy
            response.headers["Permissions-Policy"] = (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            )
            
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Additional security middleware from utils.security_middleware
    from backend.utils.security_middleware import (
        InputValidationMiddleware,
        RequestLoggingMiddleware,
    )
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Request ID Middleware (for correlation tracing)
    from starlette.middleware.base import BaseHTTPMiddleware
    import uuid

    class RequestIDMiddleware(BaseHTTPMiddleware):
        """Add X-Request-ID header for request correlation across services."""
        
        async def dispatch(self, request, call_next):
            # Generate or propagate request ID
            request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            
            # Store in request state for access in endpoints
            request.state.request_id = request_id
            # Add to logging context if available (set before calling downstream handlers)
            if hasattr(request.state, 'logger_extra'):
                request.state.logger_extra['request_id'] = request_id

            # Call downstream handlers
            response = await call_next(request)

            # Add to response headers
            response.headers["X-Request-ID"] = request_id

            return response
    
    app.add_middleware(RequestIDMiddleware)

    # Rate Limiting Middleware
    from backend.utils.rate_limiter import RateLimitMiddleware
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=redis_url,
        default_limit=100,
        default_window=60,
        strategy="sliding_window",
        skip_paths=["/health", "/", "/docs", "/redoc", "/openapi.json", "/metrics"]
    )

    allow_origin_regex = r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$" if env != "production" else None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-xsrf-token", "Location"],
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Core Monolithic Routers
    from backend.auth.routes import router as auth_router
    from backend.api.calendar import router as calendar_router
    from backend.api.users import router as users_router
    from backend.api.analytics import router as analytics_router
    from backend.api.notifications import router as notifications_router
    from backend.api.proactive import router as proactive_router
    from backend.api.event_types import router as event_types_router
    from backend.api.public import router as public_router
    from backend.api.plugins import router as plugins_router
    from backend.api.webhooks import router as webhooks_router
    from backend.services.ai import router as ai_router
    from backend.api.billing import router as billing_router
    from backend.api.ai_chat import router as ai_chat_router
    from backend.routes.calendar_routes import router as calendar_integration_router
    from backend.routes.gdpr_routes import router as gdpr_router
    from backend.api.team_routes import router as team_router
    from backend.api.integration_routes import router as integration_router
    from backend.api.email_template_routes import router as email_template_router
    from backend.api.video_conference_routes import router as video_conference_router
    from backend.api.resource_routes import router as resource_router
    from backend.api.advanced_analytics_routes import router as advanced_analytics_router
    from backend.api.automation_routes import router as automation_router
    from backend.api.monitoring import router as monitoring_router

    # Registering the new unified Authentication router
    app.include_router(auth_router, prefix="/api/v1/auth")
    
    # Registering session revocation auth router
    from backend.api.auth import router as session_auth_router
    app.include_router(session_auth_router, prefix="/api/v1/auth")


    # Registering calendar integration router
    app.include_router(calendar_integration_router)

    # Registering GDPR compliance router
    app.include_router(gdpr_router)

    # Registering team scheduling router
    app.include_router(team_router, prefix="/api/v1")

    # Registering analytics router
    app.include_router(analytics_router, prefix="/api/v1")


    # Registering integration router
    app.include_router(integration_router, prefix="/api/v1")

    # Registering email template router
    app.include_router(email_template_router, prefix="/api/v1")

    # Registering video conference router
    app.include_router(video_conference_router, prefix="/api/v1")

    # Registering resource router
    app.include_router(resource_router, prefix="/api/v1")

    # Registering advanced analytics router
    app.include_router(advanced_analytics_router, prefix="/api/v1")

    # Registering automation router
    app.include_router(automation_router, prefix="/api/v1")

    app.include_router(calendar_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    app.include_router(proactive_router, prefix="/api/v1")
    app.include_router(event_types_router, prefix="/api/v1")
    app.include_router(plugins_router, prefix="/api/v1")
    app.include_router(webhooks_router, prefix="/api/v1")
    app.include_router(public_router, prefix="/api")
    app.include_router(ai_router, prefix="/api/v1")
    app.include_router(ai_chat_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")
    app.include_router(monitoring_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "monolith"}

    @app.api_route("/", methods=["GET", "HEAD"])
    async def root():
        return {
            "app": "GraftAI",
            "status": "running",
            "frontend_url": os.getenv("FRONTEND_URL", os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")),
        }

    return app

app = create_app()
