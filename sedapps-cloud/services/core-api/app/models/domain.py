from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class DomainStatus(str, enum.Enum):
    active = "active"
    pending = "pending"
    expired = "expired"


class Domain(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("name", name="uq_domains_name"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="external", nullable=False)
    status: Mapped[DomainStatus] = mapped_column(
        Enum(DomainStatus, name="domain_status"), default=DomainStatus.active, nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parent_domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True
    )

    @property
    def verification_name(self) -> str | None:
        return f"_salaai-verify.{self.name}" if self.verification_token else None

    @property
    def verification_value(self) -> str | None:
        return (
            f"salaai-verification={self.verification_token}"
            if self.verification_token
            else None
        )
