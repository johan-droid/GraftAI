import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env")


async def migrate():
    print("🚀 Initializing Sync Schema Migration with SSL handling...")

    # Replicate the logic from backend/utils/db.py
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

    _connect_args = {}
    if _needs_ssl:
        _connect_args["ssl"] = True

    engine = create_async_engine(
        _clean_url,
        echo=False,
        future=True,
        connect_args=_connect_args,
    )

    async with engine.begin() as conn:
        # 1. Update EventTable
        print("--- Updating events table ---")
        await conn.execute(
            text("ALTER TABLE events ADD COLUMN IF NOT EXISTS external_id VARCHAR(512)")
        )
        await conn.execute(
            text("ALTER TABLE events ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(256)")
        )
        await conn.execute(
            text(
                "ALTER TABLE events ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'local'"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_events_external_id ON events (external_id)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_events_fingerprint ON events (fingerprint)"
            )
        )

        # 2. Update UserTable (Cleanup any accidental field placement)
        print("--- Cleaning up accidental fields ---")
        await conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS sync_token"))

        # 3. Update UserTokenTable
        print("--- Updating user_tokens table ---")
        await conn.execute(
            text("ALTER TABLE user_tokens ADD COLUMN IF NOT EXISTS sync_token TEXT")
        )

        print("✅ Migration Completed Successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
