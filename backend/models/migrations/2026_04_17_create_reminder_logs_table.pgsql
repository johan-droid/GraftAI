-- Create reminder_logs table to persist scheduled reminder metadata
-- Safe to run multiple times on PostgreSQL.

CREATE TABLE IF NOT EXISTS public.reminder_logs (
    id VARCHAR(100) PRIMARY KEY,
    booking_id VARCHAR(100) NOT NULL,
    reminder_type VARCHAR(20) NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    is_sent BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    is_cancelled BOOLEAN NOT NULL DEFAULT FALSE,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_reminder_logs_booking FOREIGN KEY (booking_id)
        REFERENCES public.bookings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_reminder_logs_booking_id ON public.reminder_logs (booking_id);
CREATE INDEX IF NOT EXISTS ix_reminder_logs_scheduled_time ON public.reminder_logs (scheduled_time);
