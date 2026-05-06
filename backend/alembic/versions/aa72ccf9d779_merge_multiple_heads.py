"""Merge multiple heads

Revision ID: aa72ccf9d779
Revises: b6f3d8c5a1e2, ef9c2d4b1a7e
Create Date: 2026-05-05 20:53:06.554349

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'aa72ccf9d779'
down_revision: Union[str, None] = ('b6f3d8c5a1e2', 'ef9c2d4b1a7e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
