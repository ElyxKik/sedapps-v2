from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1._auth import require_internal
from app.tasks.deploy import deploy_site

router = APIRouter()


class DeployIn(BaseModel):
    deployment_id: str
    tenant_id: str
    project_id: str
    site_version_id: str
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    custom_domain: str | None = None
    payload: dict[str, Any]


@router.post("/site", dependencies=[Depends(require_internal)])
def create_deployment(body: DeployIn) -> dict[str, str]:
    task = deploy_site.delay(body.model_dump())
    return {"task_id": task.id, "status": "queued"}
