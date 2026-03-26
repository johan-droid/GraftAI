-- Migration: Add tenant_id column to users table for Row-Level Security
-- Run this against your PostgreSQL database

ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);

-- For existing users, you may want to set a default tenant_id if applicable:
-- UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL;
