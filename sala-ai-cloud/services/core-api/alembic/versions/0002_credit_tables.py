"""add credit_wallets and credit_transactions tables

Revision ID: 0002_credit_tables
Revises: 0001_initial
Create Date: 2026-06-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_credit_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("balance_credits", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("reserved_credits", sa.Integer, nullable=False, server_default="0"),
        sa.Column("used_this_month_credits", sa.Integer, nullable=False, server_default="0"),
        sa.Column("monthly_quota_credits", sa.Integer, nullable=False, server_default="5000"),
        sa.Column("plan", sa.String(32), nullable=False, server_default="free"),
        sa.Column("reset_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_wallets_tenant", "credit_wallets", ["tenant_id"])

    op.create_table(
        "credit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_jobs.id", ondelete="SET NULL")),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        sa.Column("credits", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_transactions_tenant", "credit_transactions", ["tenant_id"])

    # RLS
    for table in ("credit_wallets", "credit_transactions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (
              current_setting('app.current_tenant', true) = ''
              OR tenant_id = current_setting('app.current_tenant', true)::uuid
            )
            WITH CHECK (
              current_setting('app.current_tenant', true) = ''
              OR tenant_id = current_setting('app.current_tenant', true)::uuid
            )
        """)


def downgrade() -> None:
    for table in ("credit_transactions", "credit_wallets"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_credit_transactions_tenant", table_name="credit_transactions")
    op.drop_table("credit_transactions")
    op.drop_index("ix_credit_wallets_tenant", table_name="credit_wallets")
    op.drop_table("credit_wallets")
