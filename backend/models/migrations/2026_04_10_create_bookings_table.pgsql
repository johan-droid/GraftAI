-- Create bookings table for public meeting bookings
-- Safe to run multiple times on PostgreSQL.

ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';

CREATE TABLE IF NOT EXISTS public.bookings (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    event_type_id VARCHAR,
    event_id VARCHAR,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    time_zone VARCHAR(50),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'confirmed',
    questions JSON,
    metadata_payload JSON,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT fk_bookings_user FOREIGN KEY(user_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_event_type FOREIGN KEY(event_type_id) REFERENCES public.event_types(id) ON DELETE SET NULL,
    CONSTRAINT fk_bookings_event FOREIGN KEY(event_id) REFERENCES public.events(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_bookings_user_id ON public.bookings(user_id);
CREATE INDEX IF NOT EXISTS ix_bookings_event_type_id ON public.bookings(event_type_id);
CREATE INDEX IF NOT EXISTS ix_bookings_event_id ON public.bookings(event_id);
CREATE INDEX IF NOT EXISTS ix_bookings_status ON public.bookings(status);
