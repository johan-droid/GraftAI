"""Add team_id to event_types

Revision ID: ef9c2d4b1a7e
Revises: 5bf775d35f35
Create Date: 2026-05-01

"""
import sqlalchemy as sa

from alembic import op

revision = "ef9c2d4b1a7e"
down_revision = "5bf775d35f35"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "event_types" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("event_types")}
    if "team_id" not in existing_columns:
        with op.batch_alter_table("event_types") as batch_op:
            batch_op.add_column(sa.Column("team_id", sa.String(length=100), nullable=True))
    if "ix_event_types_team_id" not in inspector.get_indexes("event_types"):
        op.create_index("ix_event_types_team_id", "event_types", ["team_id"], unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "event_types" not in inspector.get_table_names():
        return
    existing_indexes = {index["name"] for index in inspector.get_indexes("event_types")}
    if "ix_event_types_team_id" in existing_indexes:
        op.drop_index("ix_event_types_team_id", table_name="event_types")
    existing_columns = {column["name"] for column in inspector.get_columns("event_types")}
    if "team_id" in existing_columns:
        with op.batch_alter_table("event_types") as batch_op:
            batch_op.drop_column("team_id")
