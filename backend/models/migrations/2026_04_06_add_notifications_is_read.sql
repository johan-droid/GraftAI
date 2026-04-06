-- Migration: Add `is_read` column to `notifications` table
-- Run this against your PostgreSQL database (or include in deployment migration pipeline)

ALTER TABLE public.notifications
    ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE NOT NULL;

CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON public.notifications(is_read);

ALTER TABLE public.notifications
    ADD COLUMN IF NOT EXISTS recipient VARCHAR(255);

UPDATE public.notifications n
SET recipient = u.email
FROM public.users u
WHERE n.user_id = u.id
  AND (n.recipient IS NULL OR n.recipient = '');

UPDATE public.notifications
SET recipient = ''
WHERE recipient IS NULL;

ALTER TABLE public.notifications
    ALTER COLUMN recipient SET DEFAULT '';

ALTER TABLE public.notifications
    ALTER COLUMN recipient SET NOT NULL;

-- Optional: You may wish to backfill historical notifications as unread/read
-- Example: UPDATE public.notifications SET is_read = FALSE WHERE is_read IS NULL;
