"""Add idempotency keys table

Revision ID: add_idempotency_keys
Revises: separate_stripe_columns
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_idempotency_keys'
down_revision = 'separate_stripe_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Create idempotency keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Request fingerprint for verification
        sa.Column('request_fingerprint', sa.String(64), nullable=False),
        
        # Cached response
        sa.Column('response_body', sa.JSON(), nullable=False),
        sa.Column('status_code', sa.Integer, server_default=sa.text('200')),
        
        # TTL
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        
        # Timestamps - use server_default so DB sets the timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    # Enforce uniqueness for (user_id, key) to prevent duplicate idempotency entries
    op.create_unique_constraint('uq_idempotency_keys_user_key', 'idempotency_keys', ['user_id', 'key'])
    op.create_index('ix_idempotency_keys_expires', 'idempotency_keys', ['expires_at'])


def downgrade():
    op.drop_constraint('uq_idempotency_keys_user_key', 'idempotency_keys', type_='unique')
    op.drop_index('ix_idempotency_keys_expires', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
