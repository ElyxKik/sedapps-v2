from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    published = "published"


class Project(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    sector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.draft,
        nullable=False,
    )
    brief: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    design_tokens: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
