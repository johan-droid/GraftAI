-- Add missing soft-delete columns for models that extend SoftDeleteMixin.
-- Safe to run multiple times on PostgreSQL.

ALTER TABLE IF EXISTS public.events ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.events ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_events_is_deleted ON public.events(is_deleted);
CREATE INDEX IF NOT EXISTS ix_events_deleted_at ON public.events(deleted_at);

ALTER TABLE IF EXISTS public.bookings ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.bookings ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_bookings_is_deleted ON public.bookings(is_deleted);
CREATE INDEX IF NOT EXISTS ix_bookings_deleted_at ON public.bookings(deleted_at);

ALTER TABLE IF EXISTS public.webhook_subscriptions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.webhook_subscriptions ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_webhook_subscriptions_is_deleted ON public.webhook_subscriptions(is_deleted);
CREATE INDEX IF NOT EXISTS ix_webhook_subscriptions_deleted_at ON public.webhook_subscriptions(deleted_at);

ALTER TABLE IF EXISTS public.event_types ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.event_types ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_event_types_is_deleted ON public.event_types(is_deleted);
CREATE INDEX IF NOT EXISTS ix_event_types_deleted_at ON public.event_types(deleted_at);

ALTER TABLE IF EXISTS public.integrations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.integrations ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_integrations_is_deleted ON public.integrations(is_deleted);
CREATE INDEX IF NOT EXISTS ix_integrations_deleted_at ON public.integrations(deleted_at);

ALTER TABLE IF EXISTS public.workflows ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.workflows ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_workflows_is_deleted ON public.workflows(is_deleted);
CREATE INDEX IF NOT EXISTS ix_workflows_deleted_at ON public.workflows(deleted_at);
