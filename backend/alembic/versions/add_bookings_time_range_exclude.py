"""Add `time_range` (tsrange) to bookings and create GiST index + exclusion constraint

Revision ID: add_bookings_time_range_exclude
Revises: add_idempotency_keys
Create Date: 2026-04-19

This migration is Postgres-only. It will no-op on other dialects (SQLite).

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_bookings_time_range_exclude"
down_revision = "add_idempotency_keys"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # This migration is Postgres-specific (tsrange + GiST + exclusion constraint).
        return

    # Add timestamp-range column to match tstzrange backfill
    op.add_column(
        "bookings",
        sa.Column("time_range", postgresql.TSTZRANGE(), nullable=True),
    )

    # Backfill existing rows from start_time/end_time
    op.execute(
        "UPDATE bookings SET time_range = "
        "tstzrange(start_time, end_time) "
        "WHERE start_time IS NOT NULL AND end_time IS NOT NULL"
    )

    # Create GiST index for range queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_bookings_time_range "
        "ON bookings USING GIST (time_range)"
    )

    # Ensure the GiST operator classes are available for user_id range exclusion
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Add exclusion constraint to prevent overlapping bookings per user
    op.execute(
        "ALTER TABLE bookings ADD CONSTRAINT no_overlapping_bookings "
        "EXCLUDE USING GIST (user_id WITH =, time_range WITH &&)"
    )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Remove exclusion constraint and index, then drop column
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings")
    op.execute("DROP INDEX IF EXISTS ix_bookings_time_range")
    op.drop_column("bookings", "time_range")
