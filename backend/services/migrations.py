import os
import logging
from pathlib import Path
from sqlalchemy import create_engine

# Initialize logger
logger = logging.getLogger(__name__)

from backend.utils.db import DATABASE_URL
from backend.models.base import Base
from backend.models.tables import UserTable, EventTable
from backend.models.user_token import UserTokenTable


def _normalize_sync_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if "sslmode=" not in url:
            if "?" in url:
                url += "&sslmode=require"
            else:
                url += "?sslmode=require"
        return url
    if database_url.startswith("mysql+aiomysql://"):
        return database_url.replace("mysql+aiomysql://", "mysql+pymysql://", 1)
    return database_url


def run_migrations(db_url: str = None, migration_file: str = None):
    db_url = db_url or DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    sync_url = _normalize_sync_url(db_url)
    engine = create_engine(sync_url, future=True)

    if migration_file:
        migration_path = Path(migration_file).resolve()
        if not migration_path.exists():
            raise FileNotFoundError(f"Migrations file not found: {migration_path}")

        sql = migration_path.read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)
    else:
        # Use SQLAlchemy model metadata for cross-database schema creation.
        Base.metadata.create_all(bind=engine)

    return True


if __name__ == "__main__":
    try:
        run_migrations()
        print("✅ Database migrations were successfully applied.")
    except Exception as exc:
        logger.error(f"❌ Failed to apply migrations: {type(exc).__name__}")
        raise
