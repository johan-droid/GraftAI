import inspect
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILES = [ROOT_DIR / ".env", ROOT_DIR / ".env.local", ROOT_DIR / ".env.development", ROOT_DIR / ".env.development.local", BACKEND_DIR / ".env", BACKEND_DIR / ".env.local", BACKEND_DIR / ".env.development", BACKEND_DIR / ".env.development.local"]
if not os.environ.get("TESTING"):
    for dotenv_path in ENV_FILES:
        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path, override=False)
DATABASE_URL = os.getenv("DATABASE_URL")
AsyncSessionLocal = None
engine = None

def _normalize_sqlite_url(url: str) -> str:
    """Normalize relative SQLite URLs to a path anchored at the repository root."""
    if not url.startswith("sqlite"):
        return url
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        path_part = url[len(prefix):]
        scheme = prefix
    else:
        prefix = "sqlite:///"
        if url.startswith(prefix):
            path_part = url[len(prefix):]
            scheme = prefix
        else:
            return url
    if not path_part:
        return url
    candidate = Path(path_part)
    if candidate.drive and (not candidate.root) and path_part.startswith("/"):
        candidate = Path(path_part[1:])
    if not candidate.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        candidate = (project_root / candidate).resolve()
    return f"{scheme}{candidate.as_posix()}"
if DATABASE_URL:
    DATABASE_URL = _normalize_sqlite_url(DATABASE_URL)
    try:
        from sqlalchemy.ext.asyncio import (
            AsyncSession,
            async_sessionmaker,
            create_async_engine,
        )
        from sqlalchemy.pool import NullPool, StaticPool
        if DATABASE_URL.startswith("sqlite"):
            sqlite_engine_kwargs = {"echo": False, "future": True, "connect_args": {"check_same_thread": False}}
            if DATABASE_URL.endswith(":memory:"):
                sqlite_engine_kwargs["poolclass"] = StaticPool
            else:
                sqlite_engine_kwargs["poolclass"] = NullPool
            engine = create_async_engine(DATABASE_URL, **sqlite_engine_kwargs)
            AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        else:
            _parsed = urlparse(DATABASE_URL)
            _params = parse_qs(_parsed.query)
            is_render = os.getenv("RENDER") == "true" or "render.com" in DATABASE_URL
            is_neon = "neon.tech" in DATABASE_URL
            _needs_ssl = _params.pop("sslmode", [None])[0] in ("require", "verify-ca", "verify-full", "prefer") or is_render or is_neon
            _params.pop("channel_binding", None)
            _clean_query = urlencode({k: v[0] for k, v in _params.items()}, doseq=False)
            _clean_url = urlunparse(_parsed._replace(query=_clean_query))
            _connect_args = {"command_timeout": 30, "timeout": float(os.getenv("DB_CONNECT_TIMEOUT", "30")), "server_settings": {"application_name": "GraftAI-Production"}}
            if _needs_ssl:
                _connect_args["ssl"] = "require" if is_render or is_neon else True
            pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
            engine = create_async_engine(_clean_url, echo=False, future=True, connect_args=_connect_args, pool_pre_ping=True, pool_recycle=pool_recycle, pool_size=pool_size, max_overflow=max_overflow, pool_timeout=pool_timeout)
            AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    except Exception as e:
        logger.exception("Database engine creation failed: %s", type(e).__name__)
else:
    logger.warning("DATABASE_URL not set — database features disabled")

async def get_db():
    if AsyncSessionLocal is None:
        msg = "Database not configured. Set DATABASE_URL in your .env file."
        raise RuntimeError(msg)
    async with AsyncSessionLocal() as session:
        yield session

def get_async_session_maker():
    """Return the async session maker factory.

    Used by scripts and migration helpers that need direct session access
    outside of FastAPI dependency injection (e.g. migrate_calendar.py).
    """
    if AsyncSessionLocal is None:
        msg = "Database not configured. Set DATABASE_URL in your .env file."
        raise RuntimeError(msg)
    return AsyncSessionLocal

async def unwrap_result(value):
    """Return SQLAlchemy results uniformly across sync/async call sites."""
    if inspect.isawaitable(value):
        return await value
    return None

@asynccontextmanager
async def get_db_context():
    """Async context manager for database sessions.

    Useful in background tasks or scripts where FastAPI's Depends() is not available.
    """
    if AsyncSessionLocal is None:
        msg = "Database not configured. Set DATABASE_URL in your .env file."
        raise RuntimeError(msg)
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
