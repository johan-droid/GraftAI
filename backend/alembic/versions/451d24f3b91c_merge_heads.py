"""Merge heads

Revision ID: 451d24f3b91c
Revises: add_event_fields, c74e5b1c133e
Create Date: 2026-04-09 16:46:32.380440

"""
from collections.abc import Sequence

revision: str = "451d24f3b91c"
down_revision: str | None = ("add_event_fields", "c74e5b1c133e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
