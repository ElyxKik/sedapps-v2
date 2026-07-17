"""Add idempotent Chariow payment receipts.

Revision ID: 0010_payment_receipts
Revises: 0009_chariow_billing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_payment_receipts"
down_revision = "0009_chariow_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sale_id", sa.String(length=80), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("resend_email_id", sa.String(length=80), nullable=True),
        sa.Column("invoice_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["billing_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id"),
    )
    op.create_index("ix_payment_receipts_sale_id", "payment_receipts", ["sale_id"])
    op.create_index("ix_payment_receipts_tenant_id", "payment_receipts", ["tenant_id"])
    op.create_index("ix_payment_receipts_user_id", "payment_receipts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_receipts_user_id", table_name="payment_receipts")
    op.drop_index("ix_payment_receipts_tenant_id", table_name="payment_receipts")
    op.drop_index("ix_payment_receipts_sale_id", table_name="payment_receipts")
    op.drop_table("payment_receipts")
