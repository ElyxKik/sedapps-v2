from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    sector: str | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    slug: str
    sector: str | None
    status: ProjectStatus
    brief: dict[str, Any]
    design_tokens: dict[str, Any]

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def _ser_id(self, v: UUID) -> str:
        return str(v)


class OnboardingIn(BaseModel):
    business_name: str
    tagline: str | None = None
    description: str | None = None
    sector: str
    site_type: str = "vitrine"          # vitrine / ecommerce / blog / portfolio
    pages: list[str] = Field(default_factory=lambda: ["home", "about", "services", "contact"])
    target_audience: str | None = None
    tone: str | None = "professional"
    primary_color: str | None = None
    secondary_color: str | None = None
    font_pref: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    social: dict[str, str] = Field(default_factory=dict)
    objectives: list[str] = Field(default_factory=list)
    has_blog: bool = False


class GenerateIn(BaseModel):
    force: bool = False
    locale: str = "fr"


class JobOut(BaseModel):
    id: str
    status: str
    workflow: str


class DeployIn(BaseModel):
    site_version_id: str | None = None
    custom_domain: str | None = None


class DeploymentOut(BaseModel):
    id: str
    status: str
    domain: str | None = None
    url: str | None = None
    error: str | None = None
