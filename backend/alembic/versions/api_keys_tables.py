"""Add API key tables

Revision ID: api_keys
Revises: team_scheduling
Create Date: 2024-12-XX

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "api_keys"
down_revision = "team_scheduling"
branch_labels = None
depends_on = None


def upgrade():
    # API keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("scopes", postgresql.JSON(), default=list),
        sa.Column("rate_limit", sa.Integer(), default=1000),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), default=0),
    )

    # Create indexes
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_user_active", "api_keys", ["user_id", "is_active"])

    # API key usage table
    op.create_table(
        "api_key_usage",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "api_key_id",
            sa.String(100),
            sa.ForeignKey("api_keys.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer(), default=200),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )


def downgrade():
    op.drop_table("api_key_usage")
    op.drop_table("api_keys")
