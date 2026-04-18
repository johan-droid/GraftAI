import argparse
import asyncio
import os
import subprocess
import sys
from urllib.parse import urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.utils.db import DATABASE_URL


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


async def drop_all_tables(url: str) -> None:
    if not url:
        raise RuntimeError("DATABASE_URL not set.")

    if url.startswith("postgresql://"):
        async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(async_url)
        url_clean = urlunparse(parsed._replace(query=""))
        connect_args = {}
        is_render = os.getenv("RENDER") == "true" or "render.com" in (url or "")
        if is_render:
            connect_args["ssl"] = "require"

        engine = create_async_engine(url_clean, connect_args=connect_args)
        async with engine.begin() as conn:
            print("🔥 Dropping all tables in PostgreSQL database...")
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                quoted_tables = ", ".join(quote_identifier(t) for t in tables)
                await conn.execute(
                    text(f"DROP TABLE IF EXISTS {quoted_tables} CASCADE")
                )
                print(f"✅ Dropped {len(tables)} tables: {', '.join(tables)}")
            else:
                print("✅ No tables found to drop.")
        await engine.dispose()

    elif url.startswith("sqlite"):
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            print("🔥 Dropping all tables in SQLite database...")
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                for table in tables:
                    await conn.execute(
                        text(f"DROP TABLE IF EXISTS {quote_identifier(table)}")
                    )
                print(f"✅ Dropped {len(tables)} tables: {', '.join(tables)}")
            else:
                print("✅ No tables found to drop.")
        await engine.dispose()

    else:
        raise RuntimeError("Unsupported DATABASE_URL scheme for reset_database.py")


def run_alembic_upgrade_head() -> None:
    print("🚀 Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    if result.returncode != 0:
        raise RuntimeError("Alembic migration failed")
    print("✅ Alembic migrations applied successfully.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Reset the database by dropping all tables and optionally running Alembic migrations."
    )
    parser.add_argument(
        "--yes", action="store_true", help="Confirm database reset without prompting."
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run Alembic migrations after dropping tables.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.yes:
        print("WARNING: This will DROP ALL TABLES in the configured database.")
        confirm = input("Type 'RESET' to continue: ")
        if confirm != "RESET":
            print("Aborted.")
            sys.exit(1)

    try:
        # Ensure DATABASE_URL is present and has correct type before calling
        db_url = DATABASE_URL
        if not db_url:
            print("ERROR: DATABASE_URL not set.")
            sys.exit(1)
        asyncio.run(drop_all_tables(db_url))
        if args.migrate:
            run_alembic_upgrade_head()
        print("Database reset completed.")
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
