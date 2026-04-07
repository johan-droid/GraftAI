import logging
import hashlib
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text

# Initialize logger
logger = logging.getLogger(__name__)

from backend.utils.db import DATABASE_URL
from backend.models.base import Base


SCHEMA_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_migration_plan() -> list[Path]:
    root = _repo_root()
    manual_only = {"neon_schema_update.sql", "auth_schema.sql"}

    explicit_plan = [
        root / "backend" / "scripts" / "users_compat_patch.sql",
        root / "backend" / "models" / "migrations" / "add_tenant_id.sql",
        root / "backend" / "models" / "migrations" / "2026_04_06_add_notifications_is_read.pgsql",
        root / "backend" / "models" / "migrations" / "2026_04_07_add_quota_warning_columns.pgsql",
        root / "backend" / "models" / "migrations" / "2026_04_08_add_events_source_index.pgsql",
    ]

    discovered_pgsql = [
        p
        for p in sorted((root / "backend" / "models" / "migrations").glob("*.pgsql"))
    ]

    discovered_sql = [
        p
        for p in sorted((root / "backend" / "models" / "migrations").glob("*.sql"))
        if p.name not in manual_only
    ]

    discovered = discovered_pgsql + discovered_sql

    planned_set = {p.resolve() for p in explicit_plan}
    extras = [p for p in discovered if p.resolve() not in planned_set]

    return [p for p in explicit_plan if p.exists()] + extras


def _file_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _ensure_migration_table(engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(SCHEMA_MIGRATIONS_TABLE_SQL)


def _is_migration_applied(engine, migration_name: str, checksum: str) -> bool:
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT checksum FROM schema_migrations WHERE migration_name = :migration_name"
            ),
            {"migration_name": migration_name},
        ).fetchone()

    if row is None:
        return False

    applied_checksum = row[0]
    if applied_checksum != checksum:
        raise RuntimeError(
            f"Migration checksum mismatch for '{migration_name}'. "
            f"Expected {applied_checksum}, found {checksum}."
        )

    return True


def _record_migration(engine, migration_name: str, checksum: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO schema_migrations (migration_name, checksum)
                VALUES (:migration_name, :checksum)
                ON CONFLICT (migration_name) DO NOTHING
                """
            ),
            {"migration_name": migration_name, "checksum": checksum},
        )


def _apply_sql_file(engine, migration_path: Path) -> str:
    sql = migration_path.read_text(encoding="utf-8")
    checksum = _file_checksum(sql)
    migration_name = migration_path.name

    if _is_migration_applied(engine, migration_name, checksum):
        return f"skip:{migration_name}"

    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    _record_migration(engine, migration_name, checksum)
    return f"apply:{migration_name}"


def _normalize_sync_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
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


def run_migrations(db_url: Optional[str] = None, migration_file: Optional[str] = None):
    db_url = db_url or DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    sync_url = _normalize_sync_url(db_url)
    engine = create_engine(sync_url, future=True)

    # Create all ORM tables first so SQL patch migrations can safely alter existing relations.
    Base.metadata.create_all(bind=engine)

    # SQLite local/test mode: keep a single canonical DB path without Postgres-only SQL scripts.
    if sync_url.startswith("sqlite://"):
        return {"status": "ok", "results": ["sqlite-create-all"]}

    _ensure_migration_table(engine)

    if migration_file:
        migration_path = Path(migration_file).resolve()
        if not migration_path.exists():
            raise FileNotFoundError(f"Migrations file not found: {migration_path}")

        _apply_sql_file(engine, migration_path)
        return {"status": "ok", "applied": [migration_path.name]}
    else:
        sequence = _canonical_migration_plan()
        results = [_apply_sql_file(engine, migration) for migration in sequence]
        return {"status": "ok", "results": results}


if __name__ == "__main__":
    try:
        run_migrations()
        print("✅ Database migrations were successfully applied.")
    except Exception as exc:
        logger.error(f"❌ Failed to apply migrations: {type(exc).__name__}")
        raise
