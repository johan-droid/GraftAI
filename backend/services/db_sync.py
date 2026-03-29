import os
import logging
import asyncio
from sqlalchemy import text
from backend.utils.db import engine
from backend.models.tables import Base as ModelsBase

logger = logging.getLogger(__name__)

from sqlalchemy.orm import configure_mappers

async def sync_schema():
    """
    Autonomous database synchronization service.
    Ensures all tables and columns match the SQLAlchemy models with retry logic.
    """
    if not engine:
        logger.warning("Database engine not initialized - skipping sync")
        return

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # First, ensure all mappers are configured to prevent MapperErrors in workers
            configure_mappers()
            
            async with engine.begin() as conn:
                # 1. Create tables that don't exist
                # In development, we use create_all for simplicity. In production, use Alembic.
                await conn.run_sync(ModelsBase.metadata.create_all)
                logger.info("✅ Core tables verified")

                # 2. Patch missing columns (PostgreSQL specific)
                patches = [
                    ("events", "is_busy", "BOOLEAN", "TRUE"),
                    ("events", "category", "VARCHAR(50)", "NULL"),
                    ("events", "color", "VARCHAR(20)", "NULL"),
                    ("events", "is_meeting", "BOOLEAN", "FALSE"),
                    ("events", "meeting_platform", "VARCHAR(50)", "NULL"),
                    ("events", "meeting_link", "VARCHAR(1024)", "NULL"),
                    ("events", "is_reminded", "BOOLEAN", "FALSE"),
                    ("users", "timezone", "VARCHAR(50)", "'UTC'"),
                ]

                for table, column, col_type, default in patches:
                    try:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type} DEFAULT {default}"))
                    except Exception as patch_e:
                        logger.error(f"❌ Failed to patch {table}.{column}: {patch_e}")
                
            logger.info("✅ Database schema synchronization successful")
            return # Success!

        except Exception as e:
            if "ConnectionDoesNotExistError" in str(e) and attempt < max_retries - 1:
                logger.warning(f"⚠ Connection lost during sync (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                continue
            logger.error(f"❌ Database synchronization failed: {e}")
            raise e
