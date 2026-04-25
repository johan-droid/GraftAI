"""Add soft delete flags to critical tables

Revision ID: add_soft_delete_flags
Revises: 451d24f3b91c
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_soft_delete_flags"
down_revision = "451d24f3b91c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "events",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_events_is_deleted", "events", ["is_deleted"])

    op.add_column(
        "integrations",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "integrations",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_integrations_is_deleted", "integrations", ["is_deleted"])

    op.add_column(
        "webhook_subscriptions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "webhook_subscriptions",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_webhook_subscriptions_is_deleted",
        "webhook_subscriptions",
        ["is_deleted"],
    )


def downgrade():
    op.drop_index("ix_webhook_subscriptions_is_deleted", table_name="webhook_subscriptions")
    op.drop_column("webhook_subscriptions", "is_deleted")
    op.drop_column("webhook_subscriptions", "deleted_at")

    op.drop_index("ix_integrations_is_deleted", table_name="integrations")
    op.drop_column("integrations", "is_deleted")
    op.drop_column("integrations", "deleted_at")

    op.drop_index("ix_events_is_deleted", table_name="events")
    op.drop_column("events", "is_deleted")
    op.drop_column("events", "deleted_at")
