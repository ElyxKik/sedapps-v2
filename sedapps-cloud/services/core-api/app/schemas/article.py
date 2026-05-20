from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.models.article import ArticleStatus


class ArticleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    slug: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    content_md: str = ""
    status: ArticleStatus = ArticleStatus.draft
    scheduled_at: datetime | None = None
    seo: dict[str, Any] = Field(default_factory=dict)
    category_ids: list[str] = Field(default_factory=list)
    tag_ids: list[str] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    content_md: str | None = None
    status: ArticleStatus | None = None
    scheduled_at: datetime | None = None
    seo: dict[str, Any] | None = None


class ArticleOut(BaseModel):
    id: UUID
    slug: str
    title: str
    excerpt: str | None
    cover_url: str | None
    status: ArticleStatus
    published_at: datetime | None
    scheduled_at: datetime | None
    reading_time_min: int
    seo: dict[str, Any]

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def _ser_id(self, v: UUID) -> str:
        return str(v)
