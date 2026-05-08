#!/usr/bin/env python3
"""Verify and repair the users / user_tokens schema in backend/dev.db.

This script imports the SQLAlchemy models to determine expected columns,
compares them with SQLite's PRAGMA table_info, and issues ALTER TABLE statements
to add any missing columns (development convenience only).

Run from repository root:
  .venv\Scripts\python.exe backend\scripts\verify_user_schema.py
"""
from pathlib import Path
import sys
import sqlite3
import traceback


# Ensure repo root is on sys.path so `import backend.models.tables` works
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from typing import List

try:
    from backend.models.tables import UserTable, UserTokenTable
    from sqlalchemy import String, Text, Integer, Boolean, DateTime, JSON, Float
except Exception as e:
    print("Failed to import models:", e)
    raise


BACKEND_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BACKEND_DIR / "dev.db"


def get_actual_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}')")
    rows = cur.fetchall()
    return [r[1] for r in rows]


def add_column_sqlalchemy_column(col) -> str:
    """Map a SQLAlchemy Column to a simple SQLite column declaration.

    This intentionally keeps types conservative for SQLite (TEXT/INTEGER/DATETIME).
    """
    colname = col.name
    ctype = col.type

    # Default to TEXT
    sql_type = "TEXT"
    default_clause = ""

    try:
        if isinstance(ctype, Boolean):
            sql_type = "INTEGER"
            default_clause = "DEFAULT 0" if not col.nullable else ""
        elif isinstance(ctype, Integer):
            sql_type = "INTEGER"
            default_clause = "DEFAULT 0" if not col.nullable else ""
        elif isinstance(ctype, DateTime):
            sql_type = "DATETIME"
        elif isinstance(ctype, Float):
            sql_type = "REAL"
        elif isinstance(ctype, (String, Text, JSON)):
            sql_type = "TEXT"
        else:
            sql_type = "TEXT"
    except Exception:
        sql_type = "TEXT"

    decl = f"{colname} {sql_type} {default_clause}".strip()
    return decl


def verify_and_fix():
    if not DB_PATH.exists():
        print("Database not found at:", DB_PATH)
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    results = []

    try:
        for tbl_name, model in [("users", UserTable), ("user_tokens", UserTokenTable)]:
            print(f"\nChecking table: {tbl_name}")
            actual = get_actual_columns(conn, tbl_name)
            expected = [c.name for c in model.__table__.columns]
            print("  expected columns:", expected)
            print("  actual columns:  ", actual)

            missing = [c for c in expected if c not in actual]
            extra = [c for c in actual if c not in expected]

            if not missing:
                print("  No missing columns.")
            else:
                print("  Missing columns:", missing)
                # Add each missing column conservatively
                for col_name in missing:
                    col = model.__table__.columns.get(col_name)
                    if col is None:
                        print(f"    Could not find Column object for {col_name}; skipping")
                        continue
                    decl = add_column_sqlalchemy_column(col)
                    sql = f"ALTER TABLE {tbl_name} ADD COLUMN {decl};"
                    print("    Executing:", sql)
                    try:
                        conn.execute(sql)
                        conn.commit()
                        print(f"    Added column {col_name} to {tbl_name}")
                    except Exception as e:
                        print(f"    Failed to add column {col_name}: {e}")

            if extra:
                print("  Extra columns present in DB not in model:", extra)

            # Show final columns
            final = get_actual_columns(conn, tbl_name)
            print("  final columns:   ", final)
            results.append((tbl_name, expected, final))

        # Basic sanity: show row count and one sample user
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM users")
        cnt = cur.fetchone()[0]
        print(f"\nUsers table row count: {cnt}")
        if cnt > 0:
            cur.execute("SELECT id, email, created_at, is_superuser FROM users LIMIT 1")
            row = cur.fetchone()
            print("Sample user row:", dict(row))
        else:
            print("No users present in DB.")

    except Exception:
        traceback.print_exc()
        return 2
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    exit(verify_and_fix())
