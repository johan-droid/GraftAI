-- GraftAI Authentication Database Schema
-- This script creates the required tables for Better Auth session management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (if not exists)
-- Note: Your existing users table may have different columns, this ensures compatibility
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    emailVerified BOOLEAN DEFAULT FALSE,
    hashed_password VARCHAR(512),
    image TEXT,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional fields from your existing schema
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    tier VARCHAR(20) DEFAULT 'free' NOT NULL,
    stripe_customer_id VARCHAR(255),
    razorpay_customer_id VARCHAR(255),
    razorpay_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50) DEFAULT 'inactive',
    daily_ai_count INTEGER DEFAULT 0 NOT NULL,
    daily_sync_count INTEGER DEFAULT 0 NOT NULL,
    last_usage_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
    consent_analytics BOOLEAN DEFAULT TRUE NOT NULL,
    consent_notifications BOOLEAN DEFAULT TRUE NOT NULL,
    consent_ai_training BOOLEAN DEFAULT FALSE NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(createdAt);

-- Session table for Better Auth
CREATE TABLE IF NOT EXISTS session (
    id VARCHAR(255) PRIMARY KEY,
    userId VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expiresAt TIMESTAMP WITH TIME ZONE NOT NULL,
    ipAddress VARCHAR(50),
    userAgent TEXT,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for session lookups
CREATE INDEX IF NOT EXISTS idx_session_userId ON session(userId);
CREATE INDEX IF NOT EXISTS idx_session_expiresAt ON session(expiresAt);

-- Account table for OAuth providers
CREATE TABLE IF NOT EXISTS account (
    id VARCHAR(255) PRIMARY KEY,
    userId VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    accountId VARCHAR(255) NOT NULL,
    providerId VARCHAR(255) NOT NULL,
    accessToken TEXT,
    refreshToken TEXT,
    idToken TEXT,
    accessTokenExpiresAt TIMESTAMP WITH TIME ZONE,
    refreshTokenExpiresAt TIMESTAMP WITH TIME ZONE,
    scope TEXT,
    idTokenExpiresAt TIMESTAMP WITH TIME ZONE,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for account lookups
CREATE INDEX IF NOT EXISTS idx_account_userId ON account(userId);
CREATE INDEX IF NOT EXISTS idx_account_providerId ON account(providerId);
CREATE INDEX IF NOT EXISTS idx_account_accountId ON account(accountId);

-- Verification table for email verification and password reset tokens
CREATE TABLE IF NOT EXISTS verification (
    id VARCHAR(255) PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    expiresAt TIMESTAMP WITH TIME ZONE NOT NULL,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create index for verification lookups
CREATE INDEX IF NOT EXISTS idx_verification_identifier ON verification(identifier);
CREATE INDEX IF NOT EXISTS idx_verification_expiresAt ON verification(expiresAt);

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON TABLE session IS 'Active user sessions for Better Auth';
COMMENT ON TABLE account IS 'OAuth provider account links';
COMMENT ON TABLE verification IS 'Email verification and password reset tokens';

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON TABLE users TO your_app_user;
-- GRANT ALL PRIVILEGES ON TABLE session TO your_app_user;
-- GRANT ALL PRIVILEGES ON TABLE account TO your_app_user;
-- GRANT ALL PRIVILEGES ON TABLE verification TO your_app_user;
