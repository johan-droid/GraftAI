import os
import logging
from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure backend/.env is loaded when app is run from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.warning("⚠ DATABASE_URL not set — using SQLite in-memory fallback for local/test.")
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    try:
        from sqlalchemy.ext.asyncio import (
            AsyncSession,
            async_sessionmaker,
            create_async_engine,
        )
        from sqlalchemy.pool import NullPool, StaticPool

        if DATABASE_URL.startswith("sqlite"):
            # Keep a single connection for in-memory SQLite so metadata survives across sessions.
            sqlite_engine_kwargs = {
                "echo": False,
                "future": True,
                "connect_args": {"check_same_thread": False},
            }
            if DATABASE_URL.endswith(":memory:"):
                sqlite_engine_kwargs["poolclass"] = StaticPool
            else:
                sqlite_engine_kwargs["poolclass"] = NullPool

            engine = create_async_engine(
                DATABASE_URL,
                **sqlite_engine_kwargs,
            )
            AsyncSessionLocal = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        else:
            # asyncpg does NOT support sslmode or channel_binding as URL query params.
            # Strip them and pass ssl=True via connect_args instead.
            _parsed = urlparse(DATABASE_URL)
            _params = parse_qs(_parsed.query)
            _needs_ssl = _params.pop("sslmode", [None])[0] in (
                "require",
                "verify-ca",
                "verify-full",
                "prefer",
            )
            _params.pop("channel_binding", None)
            _clean_query = urlencode({k: v[0] for k, v in _params.items()}, doseq=False)
            _clean_url = urlunparse(_parsed._replace(query=_clean_query))

            _connect_args = {
                "command_timeout": 30, # Increased for complex AI queries
                "server_settings": {"application_name": "GraftAI-SaaS"}
            }
            if _needs_ssl:
                _connect_args["ssl"] = True

            pool_size = int(os.getenv("DB_POOL_SIZE", "40"))
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "120"))

            engine = create_async_engine(
                _clean_url,
                echo=False,
                future=True,
                connect_args=_connect_args,
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle before Neon auto-suspends (5m window)
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30,
            )
            AsyncSessionLocal = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
    except Exception as e:
        logger.error(f"⚠ Database engine creation failed: {type(e).__name__}")
else:
    logger.warning("⚠ DATABASE_URL not set — database features disabled")


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL in your .env file."
        )
    async with AsyncSessionLocal() as session:
        yield session


def maybe_await(value):
    """Resolve awaitables for robust AsyncMock and real DB result handling."""
    import inspect

    if inspect.isawaitable(value):
        return value
    return value


async def unwrap_result(value):
    """Await coroutine results if needed."""
    import inspect

    if inspect.isawaitable(value):
        return await value
    return value

