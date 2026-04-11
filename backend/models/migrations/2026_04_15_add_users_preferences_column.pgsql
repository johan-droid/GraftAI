-- Adds the users.preferences JSON column if it is missing.
-- This migration is required for production deployment because the app expects
-- UserTable.preferences to exist, but schema startup migrations only apply
-- SQL patches from backend/models/migrations.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS preferences JSON NULL;
