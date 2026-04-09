-- Create webhook subscription and webhook log tables.
-- Safe to run multiple times on PostgreSQL.

CREATE TABLE IF NOT EXISTS public.webhook_subscriptions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    events JSON NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    secret VARCHAR NOT NULL,
    external_subscription_id VARCHAR,
    client_state VARCHAR,
    last_triggered TIMESTAMPTZ,
    last_status INTEGER,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT fk_webhook_subscriptions_user FOREIGN KEY(user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_webhook_subscriptions_user_id ON public.webhook_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS ix_webhook_subscriptions_external_subscription_id ON public.webhook_subscriptions(external_subscription_id);

CREATE TABLE IF NOT EXISTS public.webhook_logs (
    id VARCHAR PRIMARY KEY,
    webhook_id VARCHAR NOT NULL,
    event VARCHAR NOT NULL,
    payload JSON NOT NULL,
    request_status INTEGER NOT NULL DEFAULT 0,
    request_error TEXT,
    attempts INTEGER NOT NULL DEFAULT 1,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT fk_webhook_logs_webhook FOREIGN KEY(webhook_id) REFERENCES public.webhook_subscriptions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_webhook_logs_webhook_id ON public.webhook_logs(webhook_id);
CREATE INDEX IF NOT EXISTS ix_webhook_logs_event ON public.webhook_logs(event);
