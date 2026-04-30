-- Backfill and enforce audit log status consistency.
-- Ensures legacy rows mirror result->status and prevents drift going forward.

BEGIN;

UPDATE audit_logs
SET status = result
WHERE status IS DISTINCT FROM result;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_audit_logs_status_matches_result'
    ) THEN
        ALTER TABLE audit_logs
            ADD CONSTRAINT ck_audit_logs_status_matches_result
            CHECK (status = result);
    END IF;
END $$;

COMMIT;
