from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class BillingPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "billing_plans"
    __table_args__ = (
        UniqueConstraint("slug", "billing_interval", name="uq_billing_plan_slug_interval"),
    )

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_interval: Mapped[str] = mapped_column(String(16), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    monthly_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    chariow_product_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
