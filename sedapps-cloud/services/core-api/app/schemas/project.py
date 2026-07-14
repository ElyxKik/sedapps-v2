from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.models.project import ProjectStatus
from app.config import settings


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    sector: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    sector: str | None = Field(None, max_length=64)
    design_tokens: dict[str, Any] | None = None
    custom_domain: str | None = Field(None, max_length=255)


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
    created_at: datetime
    default_domain: str = ""
    default_url: str = ""

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
        data.default_domain = f"{data.slug}.{settings.DEPLOY_BASE_DOMAIN}"
        data.default_url = f"https://{data.default_domain}"
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


class ComponentPatchIn(BaseModel):
    element_id: str = Field(min_length=1, max_length=120)
    ops: list[dict[str, Any]] = Field(min_length=1, max_length=50)


class ComponentPatchOut(BaseModel):
    status: Literal["ok"] = "ok"
    element: dict[str, Any]
    site_version_id: str
    version: int
    can_undo: bool
    undo_depth: int


class ComponentChatIn(BaseModel):
    element_id: str = Field(min_length=1, max_length=120)
    instruction: str = Field(min_length=1, max_length=4000)
    selected: dict[str, Any] = Field(default_factory=dict)


class ProjectChatIn(BaseModel):
    messages: list[dict[str, str]] = Field(min_length=1, max_length=50)


class PageCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    template: Literal["blank", "standard", "contact"] = "standard"


class PageUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    slug: str | None = Field(None, min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PageRegenerateIn(BaseModel):
    instruction: str = Field(default="Améliore cette page", min_length=3, max_length=2000)


class DocumentReplaceIn(BaseModel):
    document: dict[str, Any]


class ComponentCreateIn(BaseModel):
    type: Literal["Title", "Text", "Button", "Image", "Section"]
    props: dict[str, Any] = Field(default_factory=dict)
