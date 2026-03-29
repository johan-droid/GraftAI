-- Migration: Add Zoom and Meeting integration columns
-- Date: 2026-03-28

-- 1. Update 'users' table
-- Add columns one by one as they might not exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='zoom_access_token') THEN
        ALTER TABLE users ADD COLUMN zoom_access_token TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='zoom_refresh_token') THEN
        ALTER TABLE users ADD COLUMN zoom_refresh_token TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='zoom_token_expires_at') THEN
        ALTER TABLE users ADD COLUMN zoom_token_expires_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='zoom_account_id') THEN
        ALTER TABLE users ADD COLUMN zoom_account_id VARCHAR(100);
    END IF;
END $$;

-- 2. Update 'events' table
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='is_meeting') THEN
        ALTER TABLE events ADD COLUMN is_meeting BOOLEAN DEFAULT FALSE NOT NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='meeting_platform') THEN
        ALTER TABLE events ADD COLUMN meeting_platform VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='meeting_link') THEN
        ALTER TABLE events ADD COLUMN meeting_link VARCHAR(1024);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='attendees') THEN
        ALTER TABLE events ADD COLUMN attendees JSONB DEFAULT '[]'::JSONB NOT NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='agenda') THEN
        ALTER TABLE events ADD COLUMN agenda TEXT;
    END IF;
END $$;
