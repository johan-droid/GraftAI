"""Add color to event types

Revision ID: 7d9b6a4c2f11
Revises: 451d24f3b91c
Create Date: 2026-04-15

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d9b6a4c2f11"
down_revision = "451d24f3b91c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "event_types",
        sa.Column(
            "color",
            sa.String(length=7),
            nullable=False,
            server_default=sa.text("'#3b82f6'"),
        ),
    )
    op.alter_column("event_types", "color", server_default=None)


def downgrade() -> None:
    op.drop_column("event_types", "color")
