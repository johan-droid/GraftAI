"""Add automation rules tables

Revision ID: automation_rules
Revises: resource_booking
Create Date: 2024-12-XX

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "automation_rules"
down_revision = "resource_booking"
branch_labels = None
depends_on = None


def upgrade():
    # Automation rules table
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.String(100),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("conditions", postgresql.JSON(), default=dict),
        sa.Column("actions", postgresql.JSON(), default=dict),
        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("confidence_threshold", sa.Float(), default=70.0),
        sa.Column("require_confirmation", sa.Boolean(), default=False),
        sa.Column("max_executions_per_day", sa.Integer(), nullable=True),
        sa.Column("execution_count_today", sa.Integer(), default=0),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), default=50),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes
    op.create_index("ix_automation_rules_type", "automation_rules", ["rule_type"])
    op.create_index("ix_automation_rules_user", "automation_rules", ["user_id"])
    op.create_index("ix_automation_rules_team", "automation_rules", ["team_id"])
    op.create_index("ix_automation_rules_enabled", "automation_rules", ["is_enabled"])
    op.create_index(
        "ix_automation_rules_user_enabled",
        "automation_rules",
        ["user_id", "is_enabled"],
    )
    op.create_index(
        "ix_automation_rules_team_enabled",
        "automation_rules",
        ["team_id", "is_enabled"],
    )
    op.create_index(
        "ix_automation_rules_type_priority",
        "automation_rules",
        ["rule_type", "priority"],
    )

    # Automation executions table
    op.create_table(
        "automation_executions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "rule_id",
            sa.String(100),
            sa.ForeignKey("automation_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_data", postgresql.JSON(), default=dict),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("result_data", postgresql.JSON(), default=dict),
        sa.Column("confidence_score", sa.Float(), default=0.0),
        sa.Column("automation_tier", sa.String(20), default="draft"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("user_confirmed", sa.Boolean(), default=False),
        sa.Column("user_overridden", sa.Boolean(), default=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index(
        "ix_automation_executions_rule", "automation_executions", ["rule_id"]
    )
    op.create_index(
        "ix_automation_executions_status", "automation_executions", ["status"]
    )
    op.create_index(
        "ix_automation_executions_started", "automation_executions", ["started_at"]
    )

    # Automation templates table
    op.create_table(
        "automation_templates",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("template_conditions", postgresql.JSON(), default=dict),
        sa.Column("template_actions", postgresql.JSON(), default=dict),
        sa.Column("default_confidence_threshold", sa.Float(), default=70.0),
        sa.Column("default_require_confirmation", sa.Boolean(), default=True),
        sa.Column("usage_count", sa.Integer(), default=0),
        sa.Column("is_featured", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes
    op.create_index(
        "ix_automation_templates_category", "automation_templates", ["category"]
    )
    op.create_index(
        "ix_automation_templates_featured",
        "automation_templates",
        ["is_featured", "is_active"],
    )

    # Seed default templates
    bind = op.get_bind()
    if bind.engine.name == "sqlite":
        op.execute("""
            INSERT INTO automation_templates (id, name, description, category, rule_type, template_conditions, template_actions, default_confidence_threshold, default_require_confirmation, is_featured, created_at)
            VALUES
            ('auto_accept_1to1', 'Auto-Accept 1:1 Meetings', 'Automatically accept 1:1 meetings from team members', 'scheduling', 'auto_accept', '{"event_type": "1:1", "organizer_in_team": true}', '{"action": "accept", "add_to_calendar": true}', 85.0, false, true, CURRENT_TIMESTAMP),
            ('smart_scheduling', 'Smart Scheduling', 'Find optimal meeting times based on patterns', 'scheduling', 'smart_scheduling', '{"has_pattern": true}', '{"action": "suggest_times", "consider_history": true}', 75.0, true, true, CURRENT_TIMESTAMP),
            ('conflict_resolution', 'Conflict Resolution', 'Automatically resolve minor scheduling conflicts', 'conflict', 'conflict_resolution', '{"severity": "low"}', '{"action": "reschedule", "find_alternative": true}', 70.0, true, false, CURRENT_TIMESTAMP),
            ('team_sync', 'Team Sync Finder', 'Find best times for team meetings', 'team', 'team_coordination', '{"meeting_type": "team_sync"}', '{"action": "find_common_slots", "consider_timezones": true}', 80.0, true, true, CURRENT_TIMESTAMP),
            ('reminder_scheduling', 'Smart Reminders', 'Schedule optimal reminder times', 'reminder', 'reminder_scheduling', '{"event_type": "important"}', '{"action": "schedule_reminder", "timing": "optimal"}', 90.0, false, true, CURRENT_TIMESTAMP)
        """)
    else:
        op.execute("""
            INSERT INTO automation_templates (id, name, description, category, rule_type, template_conditions, template_actions, default_confidence_threshold, default_require_confirmation, is_featured, created_at)
            VALUES
            ('auto_accept_1to1', 'Auto-Accept 1:1 Meetings', 'Automatically accept 1:1 meetings from team members', 'scheduling', 'auto_accept', '{"event_type": "1:1", "organizer_in_team": true}', '{"action": "accept", "add_to_calendar": true}', 85.0, false, true, NOW()),
            ('smart_scheduling', 'Smart Scheduling', 'Find optimal meeting times based on patterns', 'scheduling', 'smart_scheduling', '{"has_pattern": true}', '{"action": "suggest_times", "consider_history": true}', 75.0, true, true, NOW()),
            ('conflict_resolution', 'Conflict Resolution', 'Automatically resolve minor scheduling conflicts', 'conflict', 'conflict_resolution', '{"severity": "low"}', '{"action": "reschedule", "find_alternative": true}', 70.0, true, false, NOW()),
            ('team_sync', 'Team Sync Finder', 'Find best times for team meetings', 'team', 'team_coordination', '{"meeting_type": "team_sync"}', '{"action": "find_common_slots", "consider_timezones": true}', 80.0, true, true, NOW()),
            ('reminder_scheduling', 'Smart Reminders', 'Schedule optimal reminder times', 'reminder', 'reminder_scheduling', '{"event_type": "important"}', '{"action": "schedule_reminder", "timing": "optimal"}', 90.0, false, true, NOW())
        """)


def downgrade():
    op.drop_table("automation_templates")
    op.drop_table("automation_executions")
    op.drop_table("automation_rules")
