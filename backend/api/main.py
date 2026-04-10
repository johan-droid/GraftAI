import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
import sentry_sdk
from fastapi import FastAPI, Request
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
    await _ensure_event_column_migrations()

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

async def _ensure_event_column_migrations():
    if not hasattr(db_utils, "engine") or db_utils.DATABASE_URL is None:
        return

    from sqlalchemy import text

    try:
        async with db_utils.engine.begin() as conn:
            if db_utils.DATABASE_URL.startswith("sqlite"):
                result = await conn.execute(text("PRAGMA table_info(events);"))
                event_columns = [row[1] for row in result.fetchall()]
                if "description" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN description TEXT;"))
                if "location" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN location TEXT;"))
                if "meeting_url" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN meeting_url TEXT;"))
                if "meeting_provider" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN meeting_provider TEXT;"))
                if "is_meeting" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN is_meeting BOOLEAN NOT NULL DEFAULT 0;"))
                if "attendees" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN attendees TEXT;"))
                if "metadata_payload" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN metadata_payload TEXT;"))
                if "event_type_id" not in event_columns:
                    await conn.execute(text("ALTER TABLE events ADD COLUMN event_type_id TEXT;"))

                result = await conn.execute(text("PRAGMA table_info(users);"))
                user_columns = [row[1] for row in result.fetchall()]
                if "username" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN username TEXT;"))
                if "email_verified" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0;"))
                if "email_verification_code" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_code TEXT;"))
                if "email_verification_expires_at" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires_at TEXT;"))
                if "tier" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN tier TEXT NOT NULL DEFAULT 'free';"))
                if "subscription_status" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN subscription_status TEXT NOT NULL DEFAULT 'inactive';"))
                if "razorpay_customer_id" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN razorpay_customer_id TEXT;"))
                if "razorpay_subscription_id" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN razorpay_subscription_id TEXT;"))
                if "daily_ai_count" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN daily_ai_count INTEGER NOT NULL DEFAULT 0;"))
                if "daily_ai_limit" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN daily_ai_limit INTEGER;"))
                if "daily_sync_count" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN daily_sync_count INTEGER NOT NULL DEFAULT 0;"))
                if "daily_sync_limit" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN daily_sync_limit INTEGER;"))
                if "quota_reset_at" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN quota_reset_at TEXT;"))
                if "trial_active" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN trial_active BOOLEAN NOT NULL DEFAULT 0;"))
                if "trial_expires_at" not in user_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN trial_expires_at TEXT;"))

                result = await conn.execute(text("PRAGMA table_info(bookings);"))
                booking_columns = [row[1] for row in result.fetchall()]
                if "is_reminder_sent" not in booking_columns:
                    await conn.execute(text("ALTER TABLE bookings ADD COLUMN is_reminder_sent BOOLEAN NOT NULL DEFAULT 0;"))
                if "booking_code" not in booking_columns:
                    await conn.execute(text("ALTER TABLE bookings ADD COLUMN booking_code TEXT;"))

                result = await conn.execute(text("PRAGMA table_info(event_types);"))
                event_type_columns = [row[1] for row in result.fetchall()]
                if "recurrence_rule" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN recurrence_rule TEXT;"))
                if "custom_questions" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN custom_questions TEXT;"))
                if "requires_attendee_confirmation" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN requires_attendee_confirmation BOOLEAN NOT NULL DEFAULT 0;"))
                if "travel_time_before_minutes" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN travel_time_before_minutes INTEGER NOT NULL DEFAULT 0;"))
                if "travel_time_after_minutes" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN travel_time_after_minutes INTEGER NOT NULL DEFAULT 0;"))
                if "requires_payment" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN requires_payment BOOLEAN NOT NULL DEFAULT 0;"))
                if "payment_amount" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN payment_amount FLOAT;"))
                if "payment_currency" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN payment_currency TEXT NOT NULL DEFAULT 'USD';"))
                if "team_assignment_method" not in event_type_columns:
                    await conn.execute(text("ALTER TABLE event_types ADD COLUMN team_assignment_method TEXT NOT NULL DEFAULT 'host_only';"))
            else:
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS description TEXT;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS location TEXT;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS meeting_url TEXT;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS meeting_provider TEXT;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS is_meeting BOOLEAN;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS attendees JSON;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS metadata_payload JSON;"))
                await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_type_id TEXT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_code TEXT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP WITH TIME ZONE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'free';"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status TEXT NOT NULL DEFAULT 'inactive';"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS razorpay_customer_id TEXT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS razorpay_subscription_id TEXT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_ai_count INTEGER NOT NULL DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_ai_limit INTEGER;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_sync_count INTEGER NOT NULL DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_sync_limit INTEGER;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS quota_reset_at TIMESTAMP WITH TIME ZONE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_active BOOLEAN NOT NULL DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP WITH TIME ZONE;"))
                await conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_reminder_sent BOOLEAN NOT NULL DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS booking_code TEXT;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS recurrence_rule TEXT;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS custom_questions JSON;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS requires_attendee_confirmation BOOLEAN NOT NULL DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS travel_time_before_minutes INTEGER NOT NULL DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS travel_time_after_minutes INTEGER NOT NULL DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS requires_payment BOOLEAN NOT NULL DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS payment_amount FLOAT;"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS payment_currency TEXT NOT NULL DEFAULT 'USD';"))
                await conn.execute(text("ALTER TABLE event_types ADD COLUMN IF NOT EXISTS team_assignment_method TEXT NOT NULL DEFAULT 'host_only';"))
    except Exception:
        # If the DB is already in the correct state or unsupported, ignore failures here
        pass

def create_app() -> FastAPI:
    app = FastAPI(
        title="GraftAI Monolith",
        description="A bare-minimum, high-performance monolithic backend for GraftAI.",
        version="2.0.0",
        lifespan=lifespan
    )

    if os.getenv("SENTRY_DSN"):
        app.add_middleware(SentryAsgiMiddleware)

    # Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; font-src 'self' data: https:; img-src 'self' data: https:; connect-src 'self' https:;"
        return response

    # Trusted Host and CORS hardening
    frontend_url = os.getenv("FRONTEND_URL", os.getenv("FRONTEND_BASE_URL", "http://localhost:3000"))
    if frontend_url:
        allow_origins = [origin.strip() for origin in frontend_url.split(",") if origin.strip()]
    else:
        allow_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    trusted_hosts = _parse_comma_separated_env("TRUSTED_HOSTS")
    if not trusted_hosts:
        env = os.getenv("ENV", "development").lower()
        if env == "production":
            trusted_hosts = [
                _extract_hostname(host)
                for host in allow_origins
                if host
            ]
            backend_host = _extract_hostname(os.getenv("BACKEND_URL") or os.getenv("APP_BASE_URL"))
            if backend_host:
                trusted_hosts.append(backend_host)
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
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Content Security Policy
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://api.graftai.tech;"
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=r"^https?://(?:localhost|127\.0\.0\.1|(?:\d{1,3}\.){3}\d{1,3})(?::\d+)?|.*\.vercel\.app$|.*\.render\.com$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-xsrf-token"],
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
    from backend.routes.calendar_routes import router as calendar_integration_router
    from backend.routes.gdpr_routes import router as gdpr_router
    from backend.api.team_routes import router as team_router
    from backend.api.analytics_routes import router as analytics_router
    from backend.api.api_key_routes import router as api_key_router
    from backend.api.integration_routes import router as integration_router
    from backend.api.email_template_routes import router as email_template_router
    from backend.api.video_conference_routes import router as video_conference_router
    from backend.api.resource_routes import router as resource_router
    from backend.api.advanced_analytics_routes import router as advanced_analytics_router
    from backend.api.automation_routes import router as automation_router

    # Registering the new unified Authentication router
    app.include_router(auth_router, prefix="/api/v1/auth")

    # Registering MFA router
    from backend.auth.mfa import router as mfa_router
    app.include_router(mfa_router, prefix="/api/v1/auth/mfa")

    # Registering calendar integration router
    app.include_router(calendar_integration_router)

    # Registering GDPR compliance router
    app.include_router(gdpr_router)

    # Registering team scheduling router
    app.include_router(team_router, prefix="/api/v1")

    # Registering analytics router
    app.include_router(analytics_router, prefix="/api/v1")

    # Registering API key router
    app.include_router(api_key_router, prefix="/api/v1")

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
    app.include_router(billing_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "monolith"}

    return app

app = create_app()
