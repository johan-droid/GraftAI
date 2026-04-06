-- Executable PostgreSQL migration (used by backend/services/migrations.py)
ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE NOT NULL;

CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS recipient VARCHAR(255) DEFAULT '' NOT NULL;

UPDATE notifications AS n
SET recipient = COALESCE(u.email, '')
FROM users AS u
WHERE n.user_id = u.id
  AND (n.recipient IS NULL OR n.recipient = '');

UPDATE notifications
SET recipient = ''
WHERE recipient IS NULL;
