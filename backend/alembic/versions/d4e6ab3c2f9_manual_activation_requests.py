"""Create manual activation requests table

Revision ID: d4e6ab3c2f9
Revises: b5f2e8c9d1a2
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e6ab3c2f9'
down_revision = 'b5f2e8c9d1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = getattr(bind.dialect, "name", None) if bind is not None else None

    # Use timezone-aware DateTime where supported
    if dialect == 'sqlite':
        dt_type = sa.DateTime()
    else:
        dt_type = sa.DateTime(timezone=True)

    op.create_table(
        'manual_activation_requests',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_tier', sa.String(50), nullable=False, server_default=sa.text("'pro'")),
        sa.Column('proof_url', sa.String(1024), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('reviewed_by', sa.String(100), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', dt_type, nullable=True),
        sa.Column('created_at', dt_type, nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_manual_activation_requests_user_id', 'manual_activation_requests', ['user_id'])
    op.create_index('ix_manual_activation_requests_status', 'manual_activation_requests', ['status'])
    op.create_index('ix_manual_activation_requests_reviewed_by', 'manual_activation_requests', ['reviewed_by'])


def downgrade() -> None:
    op.drop_index('ix_manual_activation_requests_status', table_name='manual_activation_requests')
    op.drop_index('ix_manual_activation_requests_user_id', table_name='manual_activation_requests')
    op.drop_index('ix_manual_activation_requests_reviewed_by', table_name='manual_activation_requests')
    op.drop_table('manual_activation_requests')
