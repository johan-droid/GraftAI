"""Add video conference tables

Revision ID: video_conference
Revises: email_templates
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'video_conference'
down_revision = 'email_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Video conference configs table
    op.create_table(
        'video_conference_configs',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('config', postgresql.JSON(), default=dict),
        sa.Column('default_settings', postgresql.JSON(), default=dict),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_video_configs_user_id', 'video_conference_configs', ['user_id'])
    op.create_index('ix_video_configs_provider', 'video_conference_configs', ['provider'])
    op.create_index('ix_video_configs_user_provider', 'video_conference_configs', ['user_id', 'provider'], unique=True)
    op.create_index('ix_video_configs_default', 'video_conference_configs', ['user_id', 'is_default'])
    
    # Video conference meetings table
    op.create_table(
        'video_conference_meetings',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('config_id', sa.String(100), sa.ForeignKey('video_conference_configs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('booking_id', sa.String(100), sa.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('team_booking_id', sa.String(100), sa.ForeignKey('team_bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_meeting_id', sa.String(100), nullable=False),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('join_url', sa.String(500), nullable=False),
        sa.Column('host_url', sa.String(500), nullable=True),
        sa.Column('password', sa.String(50), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(50), default="UTC"),
        sa.Column('settings', postgresql.JSON(), default=dict),
        sa.Column('status', sa.String(20), default="scheduled"),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('recording_download_url', sa.String(500), nullable=True),
        sa.Column('recording_password', sa.String(50), nullable=True),
        sa.Column('attendee_count', sa.Integer(), default=0),
        sa.Column('max_attendees', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_video_meetings_config_id', 'video_conference_meetings', ['config_id'])
    op.create_index('ix_video_meetings_booking', 'video_conference_meetings', ['booking_id'])
    op.create_index('ix_video_meetings_team_booking', 'video_conference_meetings', ['team_booking_id'])
    op.create_index('ix_video_meetings_provider_id', 'video_conference_meetings', ['provider_meeting_id'])
    op.create_index('ix_video_meetings_time', 'video_conference_meetings', ['start_time', 'status'])
    
    # Video conference recordings table
    op.create_table(
        'video_conference_recordings',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('meeting_id', sa.String(100), sa.ForeignKey('video_conference_meetings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_recording_id', sa.String(100), nullable=False),
        sa.Column('recording_type', sa.String(20), default="cloud"),
        sa.Column('play_url', sa.String(500), nullable=True),
        sa.Column('download_url', sa.String(500), nullable=True),
        sa.Column('password', sa.String(50), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_format', sa.String(10), nullable=True),
        sa.Column('status', sa.String(20), default="processing"),
        sa.Column('recording_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recording_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_video_recordings_meeting', 'video_conference_recordings', ['meeting_id'])
    op.create_index('ix_video_recordings_provider', 'video_conference_recordings', ['provider_recording_id'])


def downgrade():
    op.drop_table('video_conference_recordings')
    op.drop_table('video_conference_meetings')
    op.drop_table('video_conference_configs')
