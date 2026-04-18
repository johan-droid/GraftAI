-- Ensure the profile onboarding flow can persist preferences even on older databases.
-- This migration is intentionally idempotent and safe to re-run.

ALTER TABLE IF EXISTS users
    ADD COLUMN IF NOT EXISTS preferences JSON;

UPDATE users
SET preferences = '{}'::json
WHERE preferences IS NULL;

ALTER TABLE IF EXISTS users
    ALTER COLUMN preferences SET DEFAULT '{}'::json;
