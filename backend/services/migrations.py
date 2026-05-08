import logging
import hashlib
from pathlib import Path
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, create_engine, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

from backend.utils.db import DATABASE_URL
from backend.models.base import Base
from backend.models.tables import UserTable, UserTokenTable


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
    scripts = [root / "backend" / "scripts" / "users_compat_patch.pgsql"]
    migration_dir = root / "backend" / "models" / "migrations"

    sql_migrations = sorted([p for p in migration_dir.glob("*.pgsql") if p.is_file()])

    return [p for p in scripts + sql_migrations if p.exists()]


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


def _webhook_tables_have_wrong_id_type(engine) -> bool:
    """Check if webhook_subscriptions.id is an integer (old schema) instead of varchar."""
    try:
        insp = inspect(engine)
        if "webhook_subscriptions" not in insp.get_table_names():
            return False
        cols = {c["name"]: c for c in insp.get_columns("webhook_subscriptions")}
        id_col = cols.get("id")
        if id_col is None:
            return False
        col_type = str(id_col["type"]).upper()
        return (
            "INT" in col_type and "VARCHAR" not in col_type and "TEXT" not in col_type
        )
    except Exception as exc:
        logger.warning("Could not inspect webhook_subscriptions schema: %s", exc)
        return False


def _get_sqlite_table_columns(engine, table_name: str) -> set[str]:
    with engine.begin() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result.fetchall()}


def _sqlite_column_declaration(column) -> str:
    sql_type = "TEXT"
    default = None

    if isinstance(column.type, Boolean):
        sql_type = "INTEGER"
        default = "0"
    elif isinstance(column.type, Integer):
        sql_type = "INTEGER"
        default = "0"
    elif isinstance(column.type, Float):
        sql_type = "REAL"
        default = "0.0"
    elif isinstance(column.type, DateTime):
        sql_type = "DATETIME"
        default = "CURRENT_TIMESTAMP"
    elif isinstance(column.type, (String, Text, JSON)):
        sql_type = "TEXT"
        default = "''"

    decl = f"{column.name} {sql_type}"
    if not column.nullable:
        if default is not None:
            decl += f" DEFAULT {default}"
        decl += " NOT NULL"
    return decl


def _ensure_sqlite_model_columns(engine) -> None:
    """Add missing SQLite columns for ORM tables that cannot be created by create_all."""
    tables = [UserTable, UserTokenTable]

    with engine.begin() as conn:
        for table_obj in tables:
            table_name = table_obj.__tablename__
            existing_columns = _get_sqlite_table_columns(engine, table_name)
            if not existing_columns:
                continue

            for column in table_obj.__table__.columns:
                if column.name in existing_columns:
                    continue

                decl = _sqlite_column_declaration(column)
                logger.info(
                    "Adding missing SQLite column %s to %s: %s",
                    column.name,
                    table_name,
                    decl,
                )
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {decl}"))


def _ensure_sqlite_soft_delete_flags(engine) -> None:
    """Ensure SQLite tables have the soft-delete columns used by the ORM."""
    table_defs = {
        "events": [
            ("deleted_at", "DATETIME", True, None),
            ("is_deleted", "BOOLEAN", False, "0"),
        ],
        "integrations": [
            ("deleted_at", "DATETIME", True, None),
            ("is_deleted", "BOOLEAN", False, "0"),
        ],
        "webhook_subscriptions": [
            ("deleted_at", "DATETIME", True, None),
            ("is_deleted", "BOOLEAN", False, "0"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in table_defs.items():
            existing_columns = _get_sqlite_table_columns(engine, table_name)
            if not existing_columns:
                continue

            for column_name, column_type, nullable, default in columns:
                if column_name not in existing_columns:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    if not nullable:
                        sql += f" NOT NULL DEFAULT {default}"
                    conn.execute(text(sql))

            if "is_deleted" in {col[0] for col in columns}:
                index_name = f"ix_{table_name}_is_deleted"
                conn.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}(is_deleted)"
                    )
                )


def run_migrations(db_url: Optional[str] = None, migration_file: Optional[str] = None):
    db_url = db_url or DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    sync_url = _normalize_sync_url(db_url)
    engine = create_engine(sync_url, future=True)

    # Only drop webhook tables when they exist with the wrong integer PK type from a
    # pre-refactor schema. This is a one-time repair, not a routine drop.
    if not sync_url.startswith("sqlite://"):
        try:
            if _webhook_tables_have_wrong_id_type(engine):
                logger.warning(
                    "webhook_subscriptions.id is integer type (legacy schema) — "
                    "dropping and recreating with correct VARCHAR type."
                )
                with engine.begin() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS webhook_logs CASCADE;"))
                    conn.execute(
                        text("DROP TABLE IF EXISTS webhook_subscriptions CASCADE;")
                    )
        except Exception as exc:
            logger.warning("Pre-create_all repair check failed (non-fatal): %s", exc)

    # Create all ORM tables first so SQL patch migrations can safely alter existing relations.
    try:
        Base.metadata.create_all(bind=engine)
    except (OperationalError, ProgrammingError) as exc:
        msg = str(exc).lower()
        # Ignore only benign "already exists" errors from repeated create_all on existing schema.
        if "already exists" in msg:
            logger.warning("Non-fatal DB schema create_all error ignored: %s", exc)
        else:
            raise

    # SQLite local/test mode: keep a single canonical DB path without Postgres-only SQL scripts.
    if sync_url.startswith("sqlite://"):
        _ensure_sqlite_soft_delete_flags(engine)
        _ensure_sqlite_model_columns(engine)
        return {
            "status": "ok",
            "results": [
                "sqlite-create-all",
                "sqlite-soft-delete-fix",
                "sqlite-model-column-fix",
            ],
        }

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
        logger.info("✅ Database migrations were successfully applied.")
    except Exception as exc:
        logger.error(f"❌ Failed to apply migrations: {type(exc).__name__}")
        raise
