"""
Copy api_keys from monolith DB to auth DB.
Usage:
  MONOLITH_DATABASE_URL=postgresql://... AUTH_DATABASE_URL=postgresql://... python docs/migrations/copy_api_keys.py

This script is best run during a maintenance window. It copies active keys first.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

MONO = os.getenv("MONOLITH_DATABASE_URL") or os.getenv("DATABASE_URL")
AUTH_DB = os.getenv("AUTH_DATABASE_URL")

if not MONO or not AUTH_DB:
    print("Set MONOLITH_DATABASE_URL (or DATABASE_URL) and AUTH_DATABASE_URL")
    sys.exit(1)

mono_eng = create_engine(MONO)
auth_eng = create_engine(AUTH_DB)

COPY_SQL = """
INSERT INTO api_keys (id, name, key_hash, key_prefix, user_id, scopes, rate_limit, is_active, last_used_at, expires_at, created_at)
SELECT id, name, key_hash, key_prefix, user_id, scopes, rate_limit, is_active, last_used_at, expires_at, created_at FROM api_keys WHERE is_active = true
ON CONFLICT (id) DO NOTHING;
"""

try:
    with mono_eng.connect() as mcon, auth_eng.connect() as acon:
        trans = acon.begin()
        try:
            result = mcon.execute(text("SELECT count(*) FROM api_keys WHERE is_active = true"))
            count = result.scalar()
            print(f"Found {count} active api_keys to copy")
            acon.execute(text(COPY_SQL))
            trans.commit()
            print("Copy completed")
        except Exception as e:
            trans.rollback()
            print("Failed to copy:", e)
            raise
except SQLAlchemyError as e:
    print("DB error:", e)
    raise

print("Done")
