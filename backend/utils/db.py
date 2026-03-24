import os
from dotenv import load_dotenv

# Ensure backend/.env is loaded when app is run from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

import ssl as _ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        # asyncpg does NOT support sslmode or channel_binding as URL query params.
        # Strip them and pass ssl=True via connect_args instead.
        _parsed = urlparse(DATABASE_URL)
        _params = parse_qs(_parsed.query)
        _needs_ssl = _params.pop("sslmode", [None])[0] in ("require", "verify-ca", "verify-full", "prefer")
        _params.pop("channel_binding", None)
        _clean_query = urlencode({k: v[0] for k, v in _params.items()}, doseq=False)
        _clean_url = urlunparse(_parsed._replace(query=_clean_query))

        _connect_args = {}
        if _needs_ssl:
            _connect_args["ssl"] = True

        engine = create_async_engine(_clean_url, echo=False, future=True, connect_args=_connect_args)
        AsyncSessionLocal = sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    except Exception as e:
        print(f"⚠ Database engine creation failed: {e}")
else:
    print("⚠ DATABASE_URL not set — database features disabled")


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL in your .env file."
        )
    async with AsyncSessionLocal() as session:
        yield session
