"""Add description and location to events

Revision ID: add_event_fields
Revises:
Create Date: 2024-01-21

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_event_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add description column
    op.add_column("events", sa.Column("description", sa.Text(), nullable=True))

    # Add location column
    op.add_column("events", sa.Column("location", sa.String(), nullable=True))


def downgrade():
    # Remove location column
    op.drop_column("events", "location")

    # Remove description column
    op.drop_column("events", "description")
