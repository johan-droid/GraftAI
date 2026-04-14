"""Add onboarding flags to users

Revision ID: a1c3e5f7b9d2
Revises: 7d9b6a4c2f11
Create Date: 2026-04-15

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1c3e5f7b9d2"
down_revision = "7d9b6a4c2f11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_completed")