"""Add email templates tables

Revision ID: email_templates
Revises: integrations
Create Date: 2024-12-XX

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "email_templates"
down_revision = "integrations"
branch_labels = None
depends_on = None


def upgrade():
    # Email templates table
    op.create_table(
        "email_templates",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_system", sa.Boolean(), default=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("available_variables", postgresql.JSON(), default=list),
        sa.Column("primary_color", sa.String(7), default="#6366f1"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes
    op.create_index("ix_email_templates_slug", "email_templates", ["slug"])
    op.create_index(
        "ix_email_templates_user_slug",
        "email_templates",
        ["user_id", "slug"],
        unique=True,
    )
    op.create_index("ix_email_templates_system", "email_templates", ["is_system"])

    # Email logs table
    op.create_table(
        "email_logs",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "template_id",
            sa.String(100),
            sa.ForeignKey("email_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("cc_emails", postgresql.JSON(), nullable=True),
        sa.Column("bcc_emails", postgresql.JSON(), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(50), default="resend"),
        sa.Column("provider_message_id", sa.String(100), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), default=dict),
    )

    # Create indexes
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("ix_email_logs_to_email", "email_logs", ["to_email"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index("ix_email_logs_user_status", "email_logs", ["user_id", "status"])
    op.create_index("ix_email_logs_sent_at", "email_logs", ["sent_at"])


def downgrade():
    op.drop_table("email_logs")
    op.drop_table("email_templates")
