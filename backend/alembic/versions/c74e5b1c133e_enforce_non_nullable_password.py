"""enforce_non_nullable_password

Revision ID: c74e5b1c133e
Revises: 2ec81d6524a6
Create Date: 2026-04-08 20:57:39.245087

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c74e5b1c133e"
down_revision: str | None = "2ec81d6524a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("hashed_password", existing_type=sa.VARCHAR(), nullable=False)

def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("hashed_password", existing_type=sa.VARCHAR(), nullable=True)
