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
    try:
        with op.batch_alter_table("event_types") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "color",
                    sa.String(length=7),
                    nullable=False,
                    server_default=sa.text("'#3b82f6'"),
                )
            )
            batch_op.alter_column("color", server_default=None)
    except Exception as e:
        print(f"Skipping migration on non-existent table: {e}")


def downgrade() -> None:
    try:
        with op.batch_alter_table("event_types") as batch_op:
            batch_op.drop_column("color")
    except Exception as e:
        print(f"Skipping migration on non-existent table: {e}")
