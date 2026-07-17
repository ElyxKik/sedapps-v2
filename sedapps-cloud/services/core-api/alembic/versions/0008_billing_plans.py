"""Add managed billing plans and grant 50 monthly free credits.

Revision ID: 0008_billing_plans
Revises: 0007_real_credit_allowance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_billing_plans"
down_revision = "0007_real_credit_allowance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "organizations",
        "ai_monthly_credit_allowance",
        server_default="50",
    )
    op.execute(
        """
        UPDATE organizations
        SET ai_monthly_credit_allowance = 50
        WHERE plan = 'free'
        """
    )

    op.create_table(
        "billing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billing_interval", sa.String(length=16), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("monthly_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("stripe_price_id", sa.String(length=128), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "slug",
            "billing_interval",
            name="uq_billing_plan_slug_interval",
        ),
    )
    op.execute(
        """
        INSERT INTO billing_plans (
            id, slug, name, description, billing_interval,
            price_cents, currency, monthly_credits, is_active, sort_order
        ) VALUES (
            '00000000-0000-4000-8000-000000000050'::uuid, 'free', 'Gratuit',
            'Découvrir Sala AI avec 50 crédits renouvelés chaque mois.',
            'month', 0, 'EUR', 50, true, 0
        )
        """
    )


def downgrade() -> None:
    op.drop_table("billing_plans")
    op.alter_column(
        "organizations",
        "ai_monthly_credit_allowance",
        server_default="0",
    )
