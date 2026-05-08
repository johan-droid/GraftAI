"""add bookings.shortlink

Revision ID: 20260508_add_bookings_shortlink
Revises: 
Create Date: 2026-05-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260508_add_bookings_shortlink'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add shortlink column to bookings table
    op.add_column('bookings', sa.Column('shortlink', sa.String(), nullable=True))
    op.create_index('ix_bookings_shortlink', 'bookings', ['shortlink'])


def downgrade() -> None:
    # Drop shortlink index and column
    op.drop_index('ix_bookings_shortlink', table_name='bookings')
    op.drop_column('bookings', 'shortlink')
