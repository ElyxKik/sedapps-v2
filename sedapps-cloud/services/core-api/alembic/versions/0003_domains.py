"""Add managed domains.

Revision ID: 0003_domains
Revises: 0002_comments
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_domains"
down_revision = "0002_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    postgresql.ENUM(
        "active", "pending", "expired", name="domain_status"
    ).create(op.get_bind(), checkfirst=True)
    status = postgresql.ENUM(
        "active",
        "pending",
        "expired",
        name="domain_status",
        create_type=False,
    )
    op.create_table(
        "domains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="external"),
        sa.Column("status", status, nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("parent_domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id", ondelete="CASCADE")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_domains_name"),
    )
    op.create_index("ix_domains_tenant_id", "domains", ["tenant_id"])
    op.create_index("ix_domains_project_id", "domains", ["project_id"])


def downgrade() -> None:
    op.drop_table("domains")
    sa.Enum(name="domain_status").drop(op.get_bind(), checkfirst=True)
