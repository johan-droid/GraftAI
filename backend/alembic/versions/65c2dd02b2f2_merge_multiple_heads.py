"""Merge multiple heads

Revision ID: 65c2dd02b2f2
Revises: 20260508_add_bookings_shortlink, aa72ccf9d779
Create Date: 2026-05-08 15:44:19.018539

"""
from collections.abc import Sequence

revision: str = "65c2dd02b2f2"
down_revision: str | None = ("20260508_add_bookings_shortlink", "aa72ccf9d779")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
