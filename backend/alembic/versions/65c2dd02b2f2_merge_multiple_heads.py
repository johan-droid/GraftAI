"""Merge multiple heads

Revision ID: 65c2dd02b2f2
Revises: 20260508_add_bookings_shortlink, aa72ccf9d779
Create Date: 2026-05-08 15:44:19.018539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65c2dd02b2f2'
down_revision: Union[str, None] = ('20260508_add_bookings_shortlink', 'aa72ccf9d779')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
