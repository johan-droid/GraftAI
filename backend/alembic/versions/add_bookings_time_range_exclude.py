"""Add `time_range` (tsrange) to bookings and create GiST index + exclusion constraint

Revision ID: add_bookings_time_range_exclude
Revises: add_idempotency_keys
Create Date: 2026-04-19

This migration is Postgres-only. It will no-op on other dialects (SQLite).

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "add_bookings_time_range_exclude"
down_revision = "add_idempotency_keys"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.add_column("bookings", sa.Column("time_range", postgresql.TSTZRANGE(), nullable=True))
    op.execute("UPDATE bookings SET time_range = tstzrange(start_time, end_time) WHERE start_time IS NOT NULL AND end_time IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_bookings_time_range ON bookings USING GIST (time_range)")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("ALTER TABLE bookings ADD CONSTRAINT no_overlapping_bookings EXCLUDE USING GIST (user_id WITH =, time_range WITH &&)")

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings")
    op.execute("DROP INDEX IF EXISTS ix_bookings_time_range")
    op.drop_column("bookings", "time_range")
