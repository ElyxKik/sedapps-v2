from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1._auth import require_internal
from app.workflows.article_generation import run_article_generation
from app.workflows.site_generation import run_site_generation

router = APIRouter()


class SiteGenIn(BaseModel):
    job_id: str
    project_id: str
    tenant_id: str
    brief: dict[str, Any]
    locale: str = "fr"


class ArticleGenIn(BaseModel):
    job_id: str
    project_id: str
    tenant_id: str
    params: dict[str, Any]


@router.post("/site-generation", dependencies=[Depends(require_internal)])
def site_generation(body: SiteGenIn) -> dict[str, str]:
    task = run_site_generation.delay(
        body.job_id, body.project_id, body.tenant_id, body.brief, body.locale
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/article-generation", dependencies=[Depends(require_internal)])
def article_generation(body: ArticleGenIn) -> dict[str, str]:
    task = run_article_generation.delay(
        body.job_id, body.project_id, body.tenant_id, body.params
    )
    return {"task_id": task.id, "status": "queued"}
