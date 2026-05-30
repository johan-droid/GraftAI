"""create auth api_keys table

Revision ID: 20260530_create_auth_api_keys
Revises: 
Create Date: 2026-05-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260530_create_auth_api_keys'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_hash', sa.String(128), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scopes', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('ix_api_keys_user_active', 'api_keys', ['user_id', 'is_active'])


def downgrade():
    op.drop_index('ix_api_keys_user_active', table_name='api_keys')
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_table('api_keys')
