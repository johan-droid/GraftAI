import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv("backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL")

async def main():
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    params = urllib.parse.parse_qs(parsed.query)
    needs_ssl = params.pop("sslmode", [None])[0] in ("require", "verify-ca", "verify-full", "prefer")
    params.pop("channel_binding", None)
    clean_query = urllib.parse.urlencode({k: v[0] for k, v in params.items()}, doseq=False)
    clean_url = urllib.parse.urlunparse(parsed._replace(query=clean_query))

    connect_args = {}
    if needs_ssl:
        connect_args["ssl"] = True

    engine = create_async_engine(clean_url, echo=True, connect_args=connect_args)
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS is_meeting BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS meeting_platform VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS meeting_link VARCHAR(1024);"))
        await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS attendees JSONB DEFAULT '[]'::JSONB NOT NULL;"))
        await conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS agenda TEXT;"))
    print("Meeting schema migration successful.")

if __name__ == "__main__":
    asyncio.run(main())
