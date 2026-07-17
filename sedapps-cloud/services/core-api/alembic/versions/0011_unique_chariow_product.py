"""Ensure one Chariow product maps to exactly one billing plan.

Revision ID: 0011_unique_chariow_product
Revises: 0010_payment_receipts
"""

from alembic import op

revision = "0011_unique_chariow_product"
down_revision = "0010_payment_receipts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_billing_plan_chariow_product",
        "billing_plans",
        ["chariow_product_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_billing_plan_chariow_product",
        "billing_plans",
        type_="unique",
    )
