"""Replace Stripe plan references with Chariow licenses.

Revision ID: 0009_chariow_billing
Revises: 0008_billing_plans
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_chariow_billing"
down_revision = "0008_billing_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "billing_plans",
        "stripe_price_id",
        new_column_name="chariow_product_id",
        existing_type=sa.String(length=128),
        existing_nullable=True,
    )
    op.alter_column(
        "organizations",
        "stripe_customer_id",
        new_column_name="chariow_customer_id",
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.add_column("organizations", sa.Column("chariow_license_id", sa.String(64)))
    op.add_column("organizations", sa.Column("chariow_license_key", sa.String(255)))
    op.add_column("organizations", sa.Column("chariow_license_status", sa.String(32)))
    op.add_column(
        "organizations",
        sa.Column("chariow_license_expires_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "organizations",
        sa.Column("chariow_license_verified_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("organizations", "chariow_license_verified_at")
    op.drop_column("organizations", "chariow_license_expires_at")
    op.drop_column("organizations", "chariow_license_status")
    op.drop_column("organizations", "chariow_license_key")
    op.drop_column("organizations", "chariow_license_id")
    op.alter_column(
        "organizations",
        "chariow_customer_id",
        new_column_name="stripe_customer_id",
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "billing_plans",
        "chariow_product_id",
        new_column_name="stripe_price_id",
        existing_type=sa.String(length=128),
        existing_nullable=True,
    )
