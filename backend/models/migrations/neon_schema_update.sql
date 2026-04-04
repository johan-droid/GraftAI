-- ============================================================================
-- NEON DATABASE MIGRATION: GraftAI System Schema Update
-- Run this against your Neon PostgreSQL database to bring it to current spec
-- ============================================================================

-- 0. Ensure Postgres UUID helper functions are available for Better Auth UUID defaults.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- 1. USERS TABLE UPDATES
-- =============================================================================

-- Add Better Auth / application columns if missing.
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tenant_id INTEGER;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS image VARCHAR(1024);
ALTER TABLE public.users ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Create indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON public.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Ensure id column can handle string UUIDs for Better Auth compatibility
-- Uncomment if your current users.id is still an integer.
-- ALTER TABLE public.users ALTER COLUMN id TYPE VARCHAR(100);

-- =============================================================================
-- 2. BETTER AUTH SESSION TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.session (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_token ON public.session(token);
CREATE INDEX IF NOT EXISTS idx_session_user_id ON public.session(user_id);

-- =============================================================================
-- 3. USER PROFILE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    monthly_ai_credits INTEGER NOT NULL DEFAULT 100,
    used_ai_credits INTEGER NOT NULL DEFAULT 0,
    onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
    preferred_locale VARCHAR(20) NOT NULL DEFAULT 'en-US',
    avatar_url VARCHAR(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);

-- =============================================================================
-- 4. EVENTS TABLE CREATION
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
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

CREATE INDEX IF NOT EXISTS idx_events_user_id ON public.events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_start_time ON public.events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_category ON public.events(category);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON public.events(user_id, start_time);

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_events_updated_at ON public.events;
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =============================================================================
-- 5. ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS events_user_isolation ON public.events;
CREATE POLICY events_user_isolation ON public.events
    USING (user_id = current_setting('app.current_user_id', true));

-- =============================================================================
-- 6. VERIFY MIGRATION
-- =============================================================================

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'session'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'events'
ORDER BY ordinal_position;

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('users', 'session', 'user_profiles', 'events')
ORDER BY tablename, indexname;
