"""Require DNS ownership verification for external domains.

Revision ID: 0012_domain_verification
Revises: 0011_unique_chariow_product
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_domain_verification"
down_revision = "0011_unique_chariow_product"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("domains", sa.Column("verification_token", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("domains", "verification_token")
