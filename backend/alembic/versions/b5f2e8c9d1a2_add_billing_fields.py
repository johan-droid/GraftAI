"""Add billing fields to users

Revision ID: b5f2e8c9d1a2
Revises: 451d24f3b91c
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5f2e8c9d1a2'
down_revision = '451d24f3b91c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use conditional SQL to avoid errors if some columns/indexes already exist
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'free';")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive';")

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS razorpay_customer_id VARCHAR(255);")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS razorpay_subscription_id VARCHAR(255);")

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_ai_count INTEGER DEFAULT 0 NOT NULL;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_ai_limit INTEGER;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_sync_count INTEGER DEFAULT 0 NOT NULL;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_sync_limit INTEGER;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quota_reset_at TIMESTAMP WITH TIME ZONE;")

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_active BOOLEAN DEFAULT FALSE NOT NULL;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP WITH TIME ZONE;")

    # Ensure indexes exist for Razorpay identifiers
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_razorpay_customer_id ON users (razorpay_customer_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_razorpay_subscription_id ON users (razorpay_subscription_id);")

    # Backfill sensible defaults for any existing rows
    op.execute("UPDATE users SET tier = 'free' WHERE tier IS NULL;")
    op.execute("UPDATE users SET subscription_status = 'inactive' WHERE subscription_status IS NULL;")
    op.execute("UPDATE users SET daily_ai_count = 0 WHERE daily_ai_count IS NULL;")
    op.execute("UPDATE users SET daily_sync_count = 0 WHERE daily_sync_count IS NULL;")


def downgrade() -> None:
    # Drop created indexes and columns if they exist
    op.execute("DROP INDEX IF EXISTS ix_users_razorpay_subscription_id;")
    op.execute("DROP INDEX IF EXISTS ix_users_razorpay_customer_id;")

    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS trial_expires_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS trial_active;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS quota_reset_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS daily_sync_limit;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS daily_sync_count;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS daily_ai_limit;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS daily_ai_count;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS razorpay_subscription_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS razorpay_customer_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS subscription_status;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tier;")
