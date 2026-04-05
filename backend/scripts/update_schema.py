"""One-shot schema updater: creates all SQLAlchemy models in the configured DB.

Run this from the repo root with the project's venv active:

    .venv/Scripts/Activate.ps1
    python backend/scripts/update_schema.py

This mirrors the app lifespan behavior but exits immediately after creating tables.
"""
import asyncio
import logging

from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase

logger = logging.getLogger("update_schema")


async def _create_all():
    if not db_utils.engine:
        raise RuntimeError("Database engine not configured. Set DATABASE_URL in .env or environment.")

    async with db_utils.engine.begin() as conn:
        logger.info("Creating/updating database schema...")
        await conn.run_sync(ModelsBase.metadata.create_all)
        logger.info("Schema update complete.")


def main():
    try:
        asyncio.run(_create_all())
        print("Schema update: OK")
    except Exception as exc:
        logger.exception("Schema update failed")
        print("Schema update failed:", exc)


if __name__ == "__main__":
    main()
