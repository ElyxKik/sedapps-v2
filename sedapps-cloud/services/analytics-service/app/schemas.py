from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    tracker_id: str = Field(min_length=3, max_length=80)
    tenant_id: str | None = None
    project_id: str | None = None
    session_id: str | None = Field(default=None, max_length=120)
    event: str = Field(min_length=1, max_length=80)
    path: str | None = Field(default=None, max_length=500)
    referrer: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
