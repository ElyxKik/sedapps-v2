from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracker_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    event: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AnalyticsDailyRollup(Base):
    __tablename__ = "analytics_daily_rollups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracker_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    day: Mapped[object] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top_paths: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
