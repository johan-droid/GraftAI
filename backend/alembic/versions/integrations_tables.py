"""Add integrations tables

Revision ID: integrations
Revises: api_keys
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'integrations'
down_revision = 'api_keys'
branch_labels = None
depends_on = None


def upgrade():
    # Integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('webhook_url', sa.String(500), nullable=False),
        sa.Column('webhook_secret', sa.String(100), nullable=True),
        sa.Column('events', postgresql.JSON(), default=list),
        sa.Column('config', postgresql.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_integrations_user_id', 'integrations', ['user_id'])
    op.create_index('ix_integrations_provider', 'integrations', ['provider'])
    op.create_index('ix_integrations_user_provider', 'integrations', ['user_id', 'provider'])
    op.create_index('ix_integrations_active', 'integrations', ['is_active'])
    
    # Integration logs table
    op.create_table(
        'integration_logs',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('integration_id', sa.String(100), sa.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.String(1000), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_integration_logs_integration_id', 'integration_logs', ['integration_id'])
    op.create_index('ix_integration_logs_integration_sent', 'integration_logs', ['integration_id', 'sent_at'])
    op.create_index('ix_integration_logs_status', 'integration_logs', ['status'])


def downgrade():
    op.drop_table('integration_logs')
    op.drop_table('integrations')
