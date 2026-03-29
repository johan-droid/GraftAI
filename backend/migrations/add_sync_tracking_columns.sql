-- Migration: Add last_synced_hash to events table
-- This column is used to track the last state of AI memory synchronization.

DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='events' AND column_name='last_synced_hash') THEN
        ALTER TABLE events ADD COLUMN last_synced_hash VARCHAR(64);
    END IF;
END $$;
