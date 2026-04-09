-- Add a PostgreSQL exclusion constraint so a user cannot book overlapping time ranges.
-- This protects the booking layer even under concurrency and race conditions.

CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_no_overlap'
          AND conrelid = 'public.bookings'::regclass
    ) THEN
        ALTER TABLE public.bookings
            ADD CONSTRAINT bookings_no_overlap
            EXCLUDE USING GIST (
                user_id WITH =,
                tstzrange(start_time, end_time) WITH &&
            );
    END IF;
END$$;
