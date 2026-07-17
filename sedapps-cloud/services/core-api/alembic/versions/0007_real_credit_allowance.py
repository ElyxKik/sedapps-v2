"""Replace inferred plan quotas with a persisted allowance.

Revision ID: 0007_real_credit_allowance
Revises: 0006_backfill_credit_ledger
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_real_credit_allowance"
down_revision = "0006_backfill_credit_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "ai_monthly_credit_allowance",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "ai_monthly_credit_allowance")
