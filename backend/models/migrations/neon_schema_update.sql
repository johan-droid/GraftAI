-- ============================================================================
-- NEON DATABASE MIGRATION: GraftAI System Schema Update
-- Run this against your Neon PostgreSQL database to bring it to current spec
-- ============================================================================

-- =============================================================================
-- 1. USERS TABLE UPDATES
-- =============================================================================

-- Add tenant_id column if missing (for Row-Level Security)
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id INTEGER;

-- Create index for tenant_id for fast RLS queries
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);

-- Create index for email lookups (authentication)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Ensure id column can handle string UUIDs (if currently integer)
-- Note: Only run this if users.id is still INTEGER
-- ALTER TABLE users ALTER COLUMN id TYPE VARCHAR(100);

-- =============================================================================
-- 2. EVENTS TABLE CREATION
-- =============================================================================

-- Create events table for sovereign scheduling
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(512) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'meeting',
    color VARCHAR(20) DEFAULT '#8A2BE2',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata_payload JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_remote BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for events table
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, start_time);

-- Create trigger for updated_at timestamp on events
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 3. ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on events table
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Create policy for users to only see their own events
CREATE POLICY IF NOT EXISTS events_user_isolation ON events
    USING (user_id = current_setting('app.current_user_id', true));

-- =============================================================================
-- 4. OPTIONAL: SET DEFAULT TENANT_ID FOR EXISTING USERS
-- =============================================================================

-- Uncomment and modify if you need to assign existing users to a default tenant
-- UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL;

-- =============================================================================
-- 5. VERIFY MIGRATION
-- =============================================================================

-- Verify users table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Verify events table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'events' 
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('users', 'events') 
ORDER BY tablename, indexname;
