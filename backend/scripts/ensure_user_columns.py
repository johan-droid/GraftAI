#!/usr/bin/env python3
import os
import sqlite3
from pathlib import Path
import sys


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    base = Path(__file__).resolve().parents[1]
    env_file = base / ".env"
    if env_file.exists():
        with env_file.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("DATABASE_URL="):
                    val = line.split("=", 1)[1]
                    val = val.strip().strip('"').strip("'")
                    return val
    return None


def sqlite_db_path_from_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite:///"):
        path = url[len("sqlite+aiosqlite:///"):]
    elif url.startswith("sqlite:///"):
        path = url[len("sqlite:///"):]
    else:
        raise ValueError(f"Not a sqlite URL: {url}")
    base = Path(__file__).resolve().parents[1]
    db_path = (base / path).resolve()
    return str(db_path)


def ensure_columns(conn: sqlite3.Connection, table: str, columns_to_add: dict) -> list:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}')")
    existing = {row[1] for row in cur.fetchall()}
    added = []
    for name, sql in columns_to_add.items():
        if name not in existing:
            print(f"Adding column {name} ...")
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {sql}")
            added.append(name)
        else:
            print(f"Column {name} already exists; skipping.")
    conn.commit()
    return added


def main():
    url = get_database_url()
    if not url:
        print("DATABASE_URL not found in env or backend/.env")
        sys.exit(1)
    if not url.startswith("sqlite"):
        print("DATABASE_URL is not sqlite; aborting. url=", url)
        sys.exit(1)
    db_path = sqlite_db_path_from_url(url)
    print("Using sqlite db:", db_path)
    if not os.path.exists(db_path):
        print("DB file not found; aborting.")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    columns = {
        "is_superuser": "is_superuser INTEGER NOT NULL DEFAULT 0",
        "token_version": "token_version INTEGER NOT NULL DEFAULT 0",
        "last_login_at": "last_login_at TEXT",
        "password_changed_at": "password_changed_at TEXT",
    }
    added = ensure_columns(conn, "users", columns)
    print("Added columns:", added)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('users')")
    rows = cur.fetchall()
    print("Final users table columns:")
    for r in rows:
        print(r)
    conn.close()


if __name__ == '__main__':
    main()
