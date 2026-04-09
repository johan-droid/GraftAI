-- Add indexes to support fast availability queries for SaaS-scale workloads
-- Safe to run multiple times on PostgreSQL.

CREATE INDEX IF NOT EXISTS ix_events_user_start_end ON public.events (user_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS ix_bookings_user_start_end ON public.bookings (user_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS ix_bookings_status_user ON public.bookings (status, user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_bookings_user_start_end ON public.bookings (user_id, start_time, end_time);
