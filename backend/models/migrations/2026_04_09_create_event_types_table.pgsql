-- Create event_types table for public booking event templates
-- Safe to run multiple times on PostgreSQL.

CREATE TABLE IF NOT EXISTS public.event_types (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    meeting_provider VARCHAR(255),
    is_public BOOLEAN DEFAULT TRUE,
    buffer_before_minutes INTEGER,
    buffer_after_minutes INTEGER,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT fk_event_types_user FOREIGN KEY(user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_event_types_user_id ON public.event_types(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_event_types_user_id_slug ON public.event_types(user_id, slug);
