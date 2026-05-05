"""Add metadata_payload, scopes, and updated_at to user_tokens

Revision ID: b6f3d8c5a1e2
Revises: 59fa74f48ce2
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6f3d8c5a1e2"
down_revision: Union[str, None] = "59fa74f48ce2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_tokens",
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
    )
    op.add_column(
        "user_tokens",
        sa.Column("scopes", sa.Text(), nullable=True),
    )
    op.add_column(
        "user_tokens",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_tokens", "updated_at")
    op.drop_column("user_tokens", "scopes")
    op.drop_column("user_tokens", "metadata_payload")
