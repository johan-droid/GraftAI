import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from backend.utils.db import DATABASE_URL


async def drop_all():
    url = DATABASE_URL
    if not url:
        print("DATABASE_URL not set.")
        return

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip query params like sslmode
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    url = urlunparse(parsed._replace(query=""))

    is_render = os.getenv("RENDER") == "true" or "render.com" in (DATABASE_URL or "")
    connect_args = {}
    if is_render:
        connect_args["ssl"] = "require"

    engine = create_async_engine(url, connect_args=connect_args)

    async with engine.begin() as conn:
        print("🔥 Dropping all tables...")
        # Get all tables in the public schema
        result = await conn.execute(
            text("""
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
        """)
        )
        tables = [row[0] for row in result.fetchall()]

        if tables:
            print(f"Found tables: {', '.join(tables)}")
            # Quote table names and join with commas
            quoted_tables = ", ".join([f'"{t}"' for t in tables])
            # CASCADE drops dependent objects like indexes/foreign keys
            await conn.execute(text(f"DROP TABLE {quoted_tables} CASCADE"))
            print("✅ All tables dropped.")
        else:
            print("No tables found.")


if __name__ == "__main__":
    asyncio.run(drop_all())
