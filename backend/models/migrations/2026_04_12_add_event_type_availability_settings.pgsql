-- Add availability and exception settings to event_types for public booking scheduling
-- Safe to run multiple times on PostgreSQL.

ALTER TABLE IF EXISTS public.event_types ADD COLUMN IF NOT EXISTS minimum_notice_minutes INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS public.event_types ADD COLUMN IF NOT EXISTS availability JSON;
ALTER TABLE IF EXISTS public.event_types ADD COLUMN IF NOT EXISTS exceptions JSON;
