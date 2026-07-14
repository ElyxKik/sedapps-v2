"""Add article comments.

Revision ID: 0002_comments
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_comments"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        "spam",
        name="comment_status",
        create_type=False,
    )
    postgresql.ENUM(
        "pending", "approved", "rejected", "spam", name="comment_status"
    ).create(op.get_bind(), checkfirst=True)
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_name", sa.String(120), nullable=False),
        sa.Column("author_email", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_comments_tenant_id", "comments", ["tenant_id"])
    op.create_index("ix_comments_project_id", "comments", ["project_id"])
    op.create_index("ix_comments_article_id", "comments", ["article_id"])


def downgrade() -> None:
    op.drop_table("comments")
    sa.Enum(name="comment_status").drop(op.get_bind(), checkfirst=True)
