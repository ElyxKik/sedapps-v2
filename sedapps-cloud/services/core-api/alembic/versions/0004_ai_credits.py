"""Add persistent AI credit accounting.

Revision ID: 0004_ai_credits
Revises: 0003_domains
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_ai_credits"
down_revision = "0003_domains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("ai_credits_used", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "organizations",
        sa.Column("ai_credits_reserved", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "organizations",
        sa.Column("ai_credits_reset_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("reserved_credits", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("charged_credits", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ai_jobs",
        sa.Column("credits_settled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        """
        UPDATE organizations
        SET ai_credits_reset_at = date_trunc('month', now()) + interval '1 month'
        WHERE ai_credits_reset_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("ai_jobs", "credits_settled")
    op.drop_column("ai_jobs", "charged_credits")
    op.drop_column("ai_jobs", "reserved_credits")
    op.drop_column("organizations", "ai_credits_reset_at")
    op.drop_column("organizations", "ai_credits_reserved")
    op.drop_column("organizations", "ai_credits_used")
