from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Organization(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default="free")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_credits_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_monthly_credit_allowance: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    ai_bonus_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_credits_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
