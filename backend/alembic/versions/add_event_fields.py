"""Add description and location to events

Revision ID: add_event_fields
Revises:
Create Date: 2024-01-21

"""
import sqlalchemy as sa

from alembic import op

revision = "add_event_fields"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("events", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("events", sa.Column("location", sa.String(), nullable=True))

def downgrade():
    op.drop_column("events", "location")
    op.drop_column("events", "description")
