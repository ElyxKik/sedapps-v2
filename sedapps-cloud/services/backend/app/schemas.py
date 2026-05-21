from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ===== Auth =====
class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""
    org_name: str = ""


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    org_name: str

    class Config:
        from_attributes = True


# ===== Projects =====
class ProjectCreate(BaseModel):
    name: str
    sector: str | None = None


class OnboardingIn(BaseModel):
    business_name: str
    sector: str = ""
    brief: str = ""
    domain: str | None = None
    stack: str | None = None
    tagline: str | None = None
    description: str | None = None
    contact_email: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    font_style: str | None = None

    model_config = {"extra": "allow"}


class GenerateIn(BaseModel):
    force: bool = False
    locale: str = "fr"
    render_mode: str = "static_classic"  # "static_classic" | "astro"


class DeployIn(BaseModel):
    custom_domain: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    sector: str | None
    status: str
    brief: dict[str, Any]
    design_tokens: dict[str, Any]
    sections: list[Any]
    domain: str | None
    published_url: str | None
    preview_nonce: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    design_tokens: dict[str, Any] | None = None
    sections: list[Any] | None = None


# ===== Jobs =====
class JobOut(BaseModel):
    id: str
    job_id: str | None = None
    project_id: str
    workflow: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any]
    error: str | None
    agents: list[Any]
    tokens_in: int
    tokens_out: int
    cost_cents: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Articles =====
class ArticleCreate(BaseModel):
    title: str
    markdown: str = ""
    status: str = "draft"


class ArticleUpdate(BaseModel):
    title: str | None = None
    markdown: str | None = None
    status: str | None = None


class ArticleOut(BaseModel):
    id: str
    project_id: str
    title: str
    slug: str
    markdown: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Deployment =====
class DeploymentOut(BaseModel):
    id: str
    project_id: str
    status: str
    domain: str | None
    url: str | None


# ===== CMS =====
class FormSubmissionIn(BaseModel):
    form_name: str = "contact"
    data: dict[str, Any]


class FormSubmissionOut(BaseModel):
    id: str
    project_id: str
    form_name: str
    data: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class CommentIn(BaseModel):
    article_id: str
    author: str = "Anonyme"
    content: str


class CommentUpdate(BaseModel):
    status: str  # approved, rejected


class CommentOut(BaseModel):
    id: str
    article_id: str
    author: str
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MediaIn(BaseModel):
    filename: str
    url: str
    mime_type: str = "image/png"
    size_bytes: int = 0


class MediaOut(BaseModel):
    id: str
    project_id: str
    filename: str
    url: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class SiteFileOut(BaseModel):
    path: str
    content: str
