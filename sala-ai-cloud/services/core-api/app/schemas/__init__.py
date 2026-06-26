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


class UserUpdate(BaseModel):
    full_name: str | None = None
    org_name: str | None = None


# ===== Credits =====
class CreditWalletOut(BaseModel):
    balance_credits: int
    reserved_credits: int
    available_credits: int
    used_this_month_credits: int
    monthly_quota_credits: int
    plan: str
    reset_at: datetime | None


class CreditTransactionOut(BaseModel):
    id: str
    project_id: str | None
    job_id: str | None
    type: str
    status: str
    credits: int
    tokens: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreditEstimateIn(BaseModel):
    operation: str = "site_generation"
    tier: str = "standard"


class CreditEstimateOut(BaseModel):
    estimated_credits: int
    max_credits: int
    estimated_tokens: int
    max_tokens: int
    available_credits: int
    can_start: bool


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
    premium: bool = False

    model_config = {"extra": "allow"}


class GenerateIn(BaseModel):
    force: bool = False
    locale: str = "fr"
    render_mode: str = "static_classic"


class DeployIn(BaseModel):
    custom_domain: str | None = None


class DomainSearchIn(BaseModel):
    domain: str


class DomainSearchOut(BaseModel):
    domain: str
    available: bool
    suggestions: list[str] = []


class CustomDomainIn(BaseModel):
    domain: str


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
    site_version_id: str | None = None
    created_at: datetime | None = None


# ===== Site Versions =====
class SiteVersionOut(BaseModel):
    id: str
    project_id: str
    version: int
    label: str | None = None
    is_published: bool
    published_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RollbackIn(BaseModel):
    site_version_id: str
    custom_domain: str | None = None


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
    status: str


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
