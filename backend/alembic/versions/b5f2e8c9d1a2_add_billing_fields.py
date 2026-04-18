"""Add billing fields to users

Revision ID: b5f2e8c9d1a2
Revises: 451d24f3b91c
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5f2e8c9d1a2"
down_revision = "451d24f3b91c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use SQLAlchemy helpers so the migration works across dialects (Postgres/SQLite)
    bind = op.get_bind()
    dialect = getattr(bind.dialect, "name", None) if bind is not None else None

    # Choose appropriate DateTime type for the dialect
    if dialect == "sqlite":
        dt_type = sa.DateTime()
        bool_server_false = sa.text("0")
    else:
        dt_type = sa.DateTime(timezone=True)
        bool_server_false = sa.text("false")

    # Add columns (use server_default for non-nullable counters/flags)
    op.add_column(
        "users",
        sa.Column(
            "tier", sa.String(50), nullable=False, server_default=sa.text("'free'")
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'inactive'"),
        ),
    )

    op.add_column(
        "users", sa.Column("razorpay_customer_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("razorpay_subscription_id", sa.String(255), nullable=True)
    )

    op.add_column(
        "users",
        sa.Column(
            "daily_ai_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )
    op.add_column("users", sa.Column("daily_ai_limit", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "daily_sync_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column("users", sa.Column("daily_sync_limit", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("quota_reset_at", dt_type, nullable=True))

    op.add_column(
        "users",
        sa.Column(
            "trial_active",
            sa.Boolean(),
            nullable=False,
            server_default=bool_server_false,
        ),
    )
    op.add_column("users", sa.Column("trial_expires_at", dt_type, nullable=True))

    # Create indexes for lookup performance
    op.create_index("ix_users_razorpay_customer_id", "users", ["razorpay_customer_id"])
    op.create_index(
        "ix_users_razorpay_subscription_id", "users", ["razorpay_subscription_id"]
    )


def downgrade() -> None:
    # Drop created indexes and columns
    op.drop_index("ix_users_razorpay_subscription_id", table_name="users")
    op.drop_index("ix_users_razorpay_customer_id", table_name="users")

    op.drop_column("users", "trial_expires_at")
    op.drop_column("users", "trial_active")
    op.drop_column("users", "quota_reset_at")
    op.drop_column("users", "daily_sync_limit")
    op.drop_column("users", "daily_sync_count")
    op.drop_column("users", "daily_ai_limit")
    op.drop_column("users", "daily_ai_count")
    op.drop_column("users", "razorpay_subscription_id")
    op.drop_column("users", "razorpay_customer_id")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "tier")
