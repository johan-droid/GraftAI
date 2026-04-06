-- Executable PostgreSQL migration (used by backend/services/migrations.py)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS ai_quota_warning_sent BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS sync_quota_warning_sent BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_quota_warning_at TIMESTAMPTZ;
