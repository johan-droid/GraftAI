"""Add team scheduling tables

Revision ID: team_scheduling
Revises: gdpr_compliance
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'team_scheduling'
down_revision = 'gdpr_compliance'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    team_tables = {'teams', 'team_members', 'team_event_types', 'team_bookings'}

    # Teams table
    if 'teams' not in existing_tables:
        op.create_table(
            'teams',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('owner_id', sa.String(100), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('round_robin_enabled', sa.Boolean(), default=False),
            sa.Column('collective_availability_enabled', sa.Boolean(), default=True),
            sa.Column('require_approval', sa.Boolean(), default=False),
            sa.Column('default_booking_duration', sa.Integer(), default=30),
            sa.Column('min_booking_notice', sa.Integer(), default=4),
            sa.Column('max_booking_notice', sa.Integer(), default=168),
            sa.Column('timezone', sa.String(50), default='UTC'),
            sa.Column('business_hours', postgresql.JSON(), default=dict),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
    
    # Team members table
    if 'team_members' not in existing_tables:
        op.create_table(
            'team_members',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('team_id', sa.String(100), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('round_robin_weight', sa.Integer(), default=1),
            sa.Column('max_daily_bookings', sa.Integer(), nullable=True),
            sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint('team_id', 'user_id', name='uq_team_members_team_user'),
        )
    
    # Team event types table
    if 'team_event_types' not in existing_tables:
        op.create_table(
            'team_event_types',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('team_id', sa.String(100), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), default=30),
        sa.Column('min_duration', sa.Integer(), nullable=True),
        sa.Column('max_duration', sa.Integer(), nullable=True),
        sa.Column('available_days', postgresql.JSON(), default=list),
        sa.Column('available_hours', postgresql.JSON(), default=dict),
        sa.Column('buffer_before', sa.Integer(), default=0),
        sa.Column('buffer_after', sa.Integer(), default=0),
        sa.Column('max_bookings_per_day', sa.Integer(), nullable=True),
        sa.Column('max_bookings_per_week', sa.Integer(), nullable=True),
        sa.Column('assigned_members', postgresql.JSON(), default=list),
        sa.Column('assignment_type', sa.String(50), default='all'),
        sa.Column('booking_link_slug', sa.String(100), nullable=True, unique=True, index=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Team bookings table
    if 'team_bookings' not in existing_tables:
        op.create_table(
            'team_bookings',
            sa.Column('id', sa.String(100), primary_key=True),
            sa.Column('team_id', sa.String(100), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('event_type_id', sa.String(100), sa.ForeignKey('team_event_types.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('attendee_name', sa.String(100), nullable=False),
            sa.Column('attendee_email', sa.String(255), nullable=False),
            sa.Column('attendee_phone', sa.String(50), nullable=True),
            sa.Column('assigned_to', sa.String(100), nullable=True),
            sa.Column('status', sa.String(50), default='confirmed'),
            sa.Column('confirmation_code', sa.String(20), nullable=False, unique=True, index=True),
            sa.Column('location', sa.String(500), nullable=True),
            sa.Column('meeting_link', sa.String(500), nullable=True),
            sa.Column('meeting_password', sa.String(50), nullable=True),
            sa.Column('synced_to_google', sa.Boolean(), default=False),
            sa.Column('synced_to_outlook', sa.Boolean(), default=False),
            sa.Column('synced_to_apple', sa.Boolean(), default=False),
            sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cancellation_reason', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSON(), default=dict),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade():
    op.drop_table('team_bookings')
    op.drop_table('team_event_types')
    op.drop_table('team_members')
    op.drop_table('teams')
