"""Merge all heads

Revision ID: 59fa74f48ce2
Revises: d4e6ab3c2f9, add_soft_delete_flags, add_user_session_fields, a1c3e5f7b9d2
Create Date: 2026-04-24 01:06:06.174117

"""
from typing import Sequence, Union




# revision identifiers, used by Alembic.
revision: str = '59fa74f48ce2'
down_revision: Union[str, None] = ('d4e6ab3c2f9', 'add_soft_delete_flags', 'add_user_session_fields', 'a1c3e5f7b9d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
