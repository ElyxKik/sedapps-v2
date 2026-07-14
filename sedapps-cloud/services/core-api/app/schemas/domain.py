from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import DomainStatus


class DomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider: str
    status: DomainStatus
    expires_at: datetime | None
    parent_domain_id: uuid.UUID | None
    project_id: uuid.UUID | None
    created_at: datetime


class DomainCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    expires_at: datetime | None = None
    provider: str = Field(default="external", max_length=32)


class SubdomainCreate(BaseModel):
    label: str = Field(min_length=1, max_length=63, pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


class DomainAssign(BaseModel):
    project_id: uuid.UUID | None = None


class DomainSearchOut(BaseModel):
    domain: str
    available: bool
