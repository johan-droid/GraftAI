"""Add AI automation tracking and dead letter queue tables

Revision ID: ai_automation_and_dlq
Revises: automation_rules
Create Date: 2024-12-XX

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ai_automation_and_dlq"
down_revision = "automation_rules"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add automation fields to bookings table
    try:
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.add_column(
                sa.Column("automation_status", sa.String(50), nullable=True, default="pending"),
            )
            batch_op.add_column(
                sa.Column("automation_run_at", sa.DateTime(timezone=True), nullable=True),
            )
            batch_op.add_column(sa.Column("decision_score", sa.Integer, nullable=True))
            batch_op.add_column(sa.Column("risk_level", sa.String(50), nullable=True))

            # Create indexes for new booking columns
            batch_op.create_index("ix_bookings_automation_status", ["automation_status"])
            batch_op.create_index("ix_bookings_automation_run_at", ["automation_run_at"])
            batch_op.create_index("ix_bookings_decision_score", ["decision_score"])
            batch_op.create_index("ix_bookings_risk_level", ["risk_level"])
    except Exception as e:
        print(f"Skipping migration on non-existent table: {e}")

    # 2. Create AI automations table (tracks agent execution results)
    op.create_table(
        "ai_automations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "booking_id",
            sa.String(100),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Automation status
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        # Decision quality
        sa.Column("decision_score", sa.Integer, nullable=True),
        sa.Column("risk_assessment", sa.String(50), nullable=True),
        # Agent decisions and reasoning
        sa.Column("agent_decisions", postgresql.JSON(), nullable=True),
        # Actions executed
        sa.Column("actions_executed", postgresql.JSON(), nullable=True),
        # External service results
        sa.Column("external_results", postgresql.JSON(), nullable=True),
        # Execution metrics
        sa.Column("execution_time_ms", sa.Float, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Error tracking
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer, default=0),
        # Fallback tracking
        sa.Column("fallback_mode", sa.String(50), nullable=True),
        # Trigger source
        sa.Column("trigger_source", sa.String(50), default="api"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create indexes for ai_automations
    op.create_index("ix_ai_automations_status", "ai_automations", ["status"])
    op.create_index(
        "ix_ai_automations_booking_user", "ai_automations", ["booking_id", "user_id"]
    )
    op.create_index("ix_ai_automations_created", "ai_automations", ["created_at"])

    # 3. Create dead letter queue table
    op.create_table(
        "dead_letter_queue",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("task_id", sa.String(100), nullable=False, index=True),
        sa.Column("task_type", sa.String(100), nullable=False, index=True),
        # Original payload
        sa.Column("payload", postgresql.JSON(), nullable=False),
        # Error information
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        # Retry tracking
        sa.Column("retry_count", sa.Integer, default=0),
        sa.Column("max_retries", sa.Integer, default=3),
        # Status
        sa.Column(
            "status", sa.String(50), default="pending"
        ),  # pending, retrying, failed, resolved
        # Resolution
        sa.Column("resolution", sa.String(50), nullable=True),  # manual, auto, ignored
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Timestamps
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create indexes for dead letter queue
    op.create_index("ix_dlq_status", "dead_letter_queue", ["status"])
    op.create_index("ix_dlq_task_type", "dead_letter_queue", ["task_type"])
    op.create_index("ix_dlq_retry_count", "dead_letter_queue", ["retry_count"])
    op.create_index("ix_dlq_created_at", "dead_letter_queue", ["created_at"])
    op.create_index("ix_dlq_next_retry", "dead_letter_queue", ["next_retry_at"])


def downgrade():
    # Drop dead letter queue
    op.drop_table("dead_letter_queue")

    # Drop AI automations
    op.drop_table("ai_automations")

    try:
        with op.batch_alter_table("bookings") as batch_op:
            # Drop indexes from bookings
            batch_op.drop_index("ix_bookings_automation_status")
            batch_op.drop_index("ix_bookings_automation_run_at")
            batch_op.drop_index("ix_bookings_decision_score")
            batch_op.drop_index("ix_bookings_risk_level")

            # Drop columns from bookings
            batch_op.drop_column("automation_status")
            batch_op.drop_column("automation_run_at")
            batch_op.drop_column("decision_score")
            batch_op.drop_column("risk_level")
    except Exception as e:
        print(f"Skipping migration on non-existent table: {e}")
