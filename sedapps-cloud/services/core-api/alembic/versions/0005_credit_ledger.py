"""Add auditable per-user AI credit ledger.

Revision ID: 0005_credit_ledger
Revises: 0004_ai_credits
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_credit_ledger"
down_revision = "0004_ai_credits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("ai_bonus_credits", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ai_jobs",
        sa.Column(
            "initiated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_ai_jobs_initiated_by_user_id", "ai_jobs", ["initiated_by_user_id"]
    )
    op.create_table(
        "credit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("credits_delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("operation", sa.String(64), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("job_id", name="uq_credit_transactions_job_id"),
    )
    op.create_index(
        "ix_credit_transactions_tenant_id", "credit_transactions", ["tenant_id"]
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])
    op.create_index("ix_credit_transactions_type", "credit_transactions", ["type"])
    op.execute("ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_credit_transactions ON credit_transactions
        USING (
          current_setting('app.current_tenant', true) = ''
          OR tenant_id = current_setting('app.current_tenant', true)::uuid
        )
        WITH CHECK (
          current_setting('app.current_tenant', true) = ''
          OR tenant_id = current_setting('app.current_tenant', true)::uuid
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_credit_transactions ON credit_transactions"
    )
    op.drop_table("credit_transactions")
    op.drop_index("ix_ai_jobs_initiated_by_user_id", table_name="ai_jobs")
    op.drop_column("ai_jobs", "initiated_by_user_id")
    op.drop_column("organizations", "ai_bonus_credits")
