"""Add resource booking tables

Revision ID: resource_booking
Revises: video_conference
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'resource_booking'
down_revision = 'video_conference'
branch_labels = None
depends_on = None


def upgrade():
    # Resources table
    op.create_table(
        'resources',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('location', sa.String(200), nullable=False),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('floor', sa.String(50), nullable=True),
        sa.Column('room_number', sa.String(50), nullable=True),
        sa.Column('owner_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', sa.String(100), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('features', postgresql.JSON(), default=list),
        sa.Column('amenities', postgresql.JSON(), default=list),
        sa.Column('images', postgresql.JSON(), default=list),
        sa.Column('min_booking_duration', sa.Integer(), default=15),
        sa.Column('max_booking_duration', sa.Integer(), default=480),
        sa.Column('min_notice_hours', sa.Integer(), default=0),
        sa.Column('max_booking_days_ahead', sa.Integer(), default=30),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('timezone', sa.String(50), default="UTC"),
        sa.Column('business_hours', postgresql.JSON(), default=dict),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), default="USD"),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('approver_ids', postgresql.JSON(), default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_resources_type', 'resources', ['resource_type'])
    op.create_index('ix_resources_owner', 'resources', ['owner_id'])
    op.create_index('ix_resources_team', 'resources', ['team_id'])
    op.create_index('ix_resources_type_location', 'resources', ['resource_type', 'location'])
    op.create_index('ix_resources_team_active', 'resources', ['team_id', 'is_active'])
    
    # Resource bookings table
    op.create_table(
        'resource_bookings',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('resource_id', sa.String(100), sa.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('booking_id', sa.String(100), sa.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('team_booking_id', sa.String(100), sa.ForeignKey('team_bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(50), default="UTC"),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attendees', sa.Integer(), default=1),
        sa.Column('status', sa.String(20), default="pending"),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checked_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hourly_cost', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_resource_bookings_resource', 'resource_bookings', ['resource_id'])
    op.create_index('ix_resource_bookings_user', 'resource_bookings', ['user_id'])
    op.create_index('ix_resource_bookings_booking', 'resource_bookings', ['booking_id'])
    op.create_index('ix_resource_bookings_team_booking', 'resource_bookings', ['team_booking_id'])
    op.create_index('ix_resource_bookings_resource_time', 'resource_bookings', ['resource_id', 'start_time', 'end_time'])
    op.create_index('ix_resource_bookings_user_status', 'resource_bookings', ['user_id', 'status'])
    op.create_index('ix_resource_bookings_status', 'resource_bookings', ['status'])
    
    # Resource maintenance table
    op.create_table(
        'resource_maintenance',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('resource_id', sa.String(100), sa.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('maintenance_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), default="scheduled"),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_resource_maintenance_resource', 'resource_maintenance', ['resource_id'])
    op.create_index('ix_resource_maintenance_status', 'resource_maintenance', ['status'])


def downgrade():
    op.drop_table('resource_maintenance')
    op.drop_table('resource_bookings')
    op.drop_table('resources')
