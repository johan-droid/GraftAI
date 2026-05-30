-- Draft migration steps to move api_keys to a dedicated auth database/schema.
-- This file contains example SQL and operational commands. Review and adapt for your deployment.

-- 1) Create new auth database (example for Postgres):
-- On primary DB host:
-- CREATE DATABASE graftai_auth WITH OWNER = current_user;

-- 2) In the new auth DB, create the api_keys table schema (copy of existing):
-- (Use Alembic in the auth service repository to manage migrations)

-- Example table (mirror of current):
CREATE TABLE IF NOT EXISTS api_keys (
  id VARCHAR(100) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  key_hash VARCHAR(128) NOT NULL UNIQUE,
  key_prefix VARCHAR(64) NOT NULL,
  user_id VARCHAR(100) NOT NULL,
  scopes JSONB DEFAULT '[]',
  rate_limit INTEGER DEFAULT 1000,
  is_active BOOLEAN DEFAULT TRUE,
  last_used_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_api_keys_key_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS ix_api_keys_user_active ON api_keys(user_id, is_active);

-- 3) Copy data from monolith DB to auth DB (example using pg_dump/pg_restore or dblink)
-- Option A: Controlled copy with minimal downtime
-- BEGIN TRANSACTION on monolith
-- INSERT INTO graftai_auth.api_keys (...) SELECT ... FROM api_keys WHERE ...;
-- COMMIT

-- 4) Switch read path: update auth verification to query the new auth DB connection string (ENV var AUTH_DATABASE_URL)
-- 5) Split write path: make API key creation endpoints write to new auth DB only (or write to both during migration window)

-- 6) Validate and cutover: ensure no writes are happening to old table (or backfill delta), then drop or archive the old table.

-- Notes:
-- - Preserve key_hash values exactly (do not re-hash) to avoid breaking client keys.
-- - If you change hashing algorithm, re-issue keys and provide a transition period accepting both algorithms.
-- - Consider replication or logical replication for zero-downtime migrations.
-- - Use a small migration script to copy active keys first, then copy deltas, then switch reads.
