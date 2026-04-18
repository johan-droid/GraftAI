"""Separate Stripe customer/subscription columns from Razorpay

Revision ID: separate_stripe_columns
Revises: add_ai_automation_and_dlq
Create Date: 2024-12-XX

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "separate_stripe_columns"
down_revision = "ai_automation_and_dlq"
branch_labels = None
depends_on = None


def upgrade():
    # Add separate Stripe columns
    op.add_column(
        "users", sa.Column("stripe_customer_id", sa.String(100), nullable=True)
    )
    op.add_column(
        "users", sa.Column("stripe_subscription_id", sa.String(100), nullable=True)
    )

    # Create indexes for Stripe columns
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"])
    op.create_index(
        "ix_users_stripe_subscription_id", "users", ["stripe_subscription_id"]
    )


def downgrade():
    # Drop Stripe columns
    op.drop_index("ix_users_stripe_subscription_id", table_name="users")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
