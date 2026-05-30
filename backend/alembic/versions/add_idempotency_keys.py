"""Add idempotency keys table

Revision ID: add_idempotency_keys
Revises: separate_stripe_columns
Create Date: 2024-12-XX

"""
import sqlalchemy as sa

from alembic import op

revision = "add_idempotency_keys"
down_revision = "separate_stripe_columns"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("idempotency_keys", sa.Column("id", sa.String(100), primary_key=True), sa.Column("key", sa.String(100), nullable=False, index=True), sa.Column("user_id", sa.String(100), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("request_fingerprint", sa.String(64), nullable=False), sa.Column("response_body", sa.JSON(), nullable=False), sa.Column("status_code", sa.Integer, server_default=sa.text("200")), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    try:
        with op.batch_alter_table("idempotency_keys") as batch_op:
            batch_op.create_unique_constraint("uq_idempotency_keys_user_key", ["user_id", "key"])
            batch_op.create_index("ix_idempotency_keys_expires", ["expires_at"])
    except Exception:
        pass

def downgrade():
    try:
        with op.batch_alter_table("idempotency_keys") as batch_op:
            batch_op.drop_constraint("uq_idempotency_keys_user_key", type_="unique")
            batch_op.drop_index("ix_idempotency_keys_expires")
    except Exception:
        pass
    op.drop_table("idempotency_keys")
