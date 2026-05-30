"""add_hashed_password

Revision ID: 2ec81d6524a6
Revises: 2c380a947a3a
Create Date: 2026-04-08 20:46:14.499490

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2ec81d6524a6"
down_revision: str | None = "2c380a947a3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "hashed_password")
