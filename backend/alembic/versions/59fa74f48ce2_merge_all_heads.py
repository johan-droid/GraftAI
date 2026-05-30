"""Merge all heads

Revision ID: 59fa74f48ce2
Revises: d4e6ab3c2f9, add_soft_delete_flags, add_user_session_fields, a1c3e5f7b9d2
Create Date: 2026-04-24 01:06:06.174117

"""
from collections.abc import Sequence

revision: str = "59fa74f48ce2"
down_revision: str | None = ("d4e6ab3c2f9", "add_soft_delete_flags", "add_user_session_fields", "a1c3e5f7b9d2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
