from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class CreditWallet(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "credit_wallets"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    balance_credits: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    reserved_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_this_month_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_quota_credits: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    plan: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CreditTransaction(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "credit_transactions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_jobs.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="completed")
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
