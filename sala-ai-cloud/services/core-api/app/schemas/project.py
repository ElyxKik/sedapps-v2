from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    sector: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    design_tokens: dict[str, Any] | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    slug: str
    sector: str | None
    status: ProjectStatus
    brief: dict[str, Any]
    design_tokens: dict[str, Any]
    custom_domain: str | None
    preview_nonce: str | None = None
    active_job_id: UUID | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def _ser_id(self, v: UUID) -> str:
        return str(v)

    @field_serializer("active_job_id")
    def _ser_active_job_id(self, v: UUID | None) -> str | None:
        return str(v) if v else None

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "ProjectOut":
        data = super().model_validate(obj, *args, **kwargs)
        if not data.preview_nonce:
            data.preview_nonce = data.slug
        return data


class OnboardingIn(BaseModel):
    business_name: str
    tagline: str | None = None
    description: str | None = None
    sector: str
    site_type: str = "vitrine"  # vitrine / ecommerce / blog / portfolio
    pages: list[str] = Field(default_factory=lambda: ["home", "about", "services", "contact"])
    target_audience: str | None = None
    tone: str | None = "professional"
    primary_color: str | None = None
    secondary_color: str | None = None
    font_pref: str | None = Field(None, alias="font_style")
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    social: dict[str, str] = Field(default_factory=dict)
    objectives: list[str] = Field(default_factory=list)
    has_blog: bool = False
    custom_domain: str | None = Field(None, alias="domain")
    premium: bool = Field(False, alias="isPremium")
    # onepage / multipage selection from onboarding
    stack: Literal["onepage", "multipage"] = Field("onepage", alias="site_stack")

    @field_validator("objectives", mode="before")
    @classmethod
    def _coerce_objectives(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        return v

    @field_validator("stack", mode="before")
    @classmethod
    def normalize_stack(cls, v: Any) -> str:
        if isinstance(v, str):
            val = v.strip().lower()
            if val in {"monopage", "onepage", "one-page", "singlepage", "single-page"}:
                return "onepage"
            if val in {"multipage", "multi-page", "multi"}:
                return "multipage"
        return v

    # Accept extra fields from the frontend and allow population by aliases or field names
    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


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
    site_version_id: str | None = None
    created_at: datetime | None = None


class SiteVersionOut(BaseModel):
    id: str
    version: int
    label: str | None = None
    is_published: bool
    published_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RollbackIn(BaseModel):
    site_version_id: str
    custom_domain: str | None = None
