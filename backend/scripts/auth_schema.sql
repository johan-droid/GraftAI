-- GraftAI Authentication Database Schema
-- Aligns the auth schema with Better Auth expectations and app-specific profile storage.

-- Ensure pgcrypto is available for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Better Auth users table compatibility
CREATE TABLE IF NOT EXISTS public.users (
    id VARCHAR(100) PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    image VARCHAR(1024),
    hashed_password VARCHAR(512),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    tier VARCHAR(20) DEFAULT 'free' NOT NULL,
    stripe_customer_id VARCHAR(255),
    razorpay_customer_id VARCHAR(255),
    razorpay_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50) DEFAULT 'inactive',
    daily_ai_count INTEGER DEFAULT 0 NOT NULL,
    daily_sync_count INTEGER DEFAULT 0 NOT NULL,
    last_usage_reset TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
    consent_analytics BOOLEAN DEFAULT TRUE NOT NULL,
    consent_notifications BOOLEAN DEFAULT TRUE NOT NULL,
    consent_ai_training BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);

CREATE TABLE IF NOT EXISTS public.session (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_token ON public.session(token);
CREATE INDEX IF NOT EXISTS idx_session_user_id ON public.session(user_id);

CREATE TABLE IF NOT EXISTS public.account (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    id_token TEXT,
    access_token_expires_at TIMESTAMPTZ,
    refresh_token_expires_at TIMESTAMPTZ,
    scope TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_account_user_id ON public.account(user_id);
CREATE INDEX IF NOT EXISTS idx_account_provider_id ON public.account(provider_id);
CREATE INDEX IF NOT EXISTS idx_account_account_id ON public.account(account_id);

CREATE TABLE IF NOT EXISTS public.verification (
    id TEXT PRIMARY KEY,
    identifier TEXT NOT NULL,
    value TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_verification_identifier ON public.verification(identifier);
CREATE INDEX IF NOT EXISTS idx_verification_expires_at ON public.verification(expires_at);

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

COMMENT ON TABLE public.user_profiles IS 'App-specific SaaS data decoupled from Better Auth users table';
COMMENT ON TABLE public.session IS 'Better Auth managed session tokens (snake_case columns)';

-- Enable RLS on events so Better Auth tenant isolation can be enforced in application code.
ALTER TABLE IF EXISTS public.events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS events_user_isolation ON public.events;
CREATE POLICY events_user_isolation ON public.events
    USING (user_id = current_setting('app.current_user_id', true));

-- Note: set app.current_user_id per connection in application code:
--   SET LOCAL app.current_user_id = '<uuid>';
