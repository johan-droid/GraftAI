"""Add usage tracking columns

Revision ID: ac0a38e31855
Revises: dccb1cf21fdd
Create Date: 2026-04-25 13:02:28.639557

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ac0a38e31855"
down_revision: str | None = "dccb1cf21fdd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("total_ai_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("total_api_calls", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("total_scheduling_count", sa.Integer(), nullable=False, server_default=sa.text("0")))

def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("total_scheduling_count")
        batch_op.drop_column("total_api_calls")
        batch_op.drop_column("total_ai_tokens")
