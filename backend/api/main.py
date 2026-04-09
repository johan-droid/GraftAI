import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (creates tables if they don't exist in monolith mode)
    run_migrations()
    await _ensure_event_column_migrations()
    yield
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

    # Simplified CORS for single-domain deployments
    frontend_url = os.getenv("FRONTEND_URL", os.getenv("FRONTEND_BASE_URL", "https://www.graftai.tech"))
    if frontend_url:
        allow_origins = [origin.strip() for origin in frontend_url.split(",") if origin.strip()]
    else:
        allow_origins = [
            "https://www.graftai.tech",
            "https://graftai.tech",
        ]

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
    from backend.api.webhooks import router as webhooks_router
    from backend.services.ai import router as ai_router

    # Registering the new unified Authentication router
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(calendar_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    app.include_router(proactive_router, prefix="/api/v1")
    app.include_router(event_types_router, prefix="/api/v1")
    app.include_router(webhooks_router, prefix="/api/v1")
    app.include_router(public_router, prefix="/api")
    app.include_router(ai_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "monolith"}

    return app

app = create_app()
