from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.ai_job import AgentRun, AiJob, JobStatus
from app.models.deployment import Deployment, DeploymentStatus
from app.models.project import Project, ProjectStatus
from app.models.site_version import SiteVersion

router = APIRouter()


def require_internal(token: str = Header(default="", alias="X-Internal-Token")) -> None:
    if token != settings.INTERNAL_API_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "internal only")


class AgentRunIn(BaseModel):
    agent_name: str
    model: str
    prompt_version: int = 1
    status: str = "ok"
    duration_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    input: dict[str, Any] = {}
    output: dict[str, Any] = {}
    warnings: list[str] = []


class JobCompleteIn(BaseModel):
    status: JobStatus
    error: str | None = None
    output: dict[str, Any] = {}
    tokens_in: int = 0
    tokens_out: int = 0
    cost_cents: int = 0


class DeploymentUpdateIn(BaseModel):
    status: DeploymentStatus
    domain: str | None = None
    url: str | None = None
    error: str | None = None
    prefix: str | None = None
    upload: dict[str, Any] | None = None
    dns: dict[str, Any] | None = None
    dry_run: bool | None = None


class JobEventIn(BaseModel):
    step: str
    label: str
    status: str = "running"
    progress: int = 0


def _append_job_event(job: AiJob, event: dict[str, Any]) -> None:
    data = dict(job.input or {})
    events = list(data.get("events") or [])
    events.append(event)
    data["events"] = events
    job.input = data


@router.post("/jobs/{job_id}/start", dependencies=[Depends(require_internal)])
def start_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)
    _append_job_event(
        job,
        {
            "step": "init",
            "label": "Initialisation du projet",
            "status": "running",
            "progress": 5,
        },
    )
    db.commit()
    return {"ok": True}


@router.post("/jobs/{job_id}/events", dependencies=[Depends(require_internal)])
def record_job_event(job_id: uuid.UUID, body: JobEventIn, db: Session = Depends(get_db)) -> dict:
    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    _append_job_event(job, body.model_dump())
    db.commit()
    return {"ok": True}


@router.post("/jobs/{job_id}/agent-runs", dependencies=[Depends(require_internal)])
def record_agent_run(job_id: uuid.UUID, body: AgentRunIn, db: Session = Depends(get_db)) -> dict:
    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    run = AgentRun(job_id=job.id, **body.model_dump())
    db.add(run)
    progress_by_agent = {
        "designer": 18,
        "copywriter": 34,
        "seo": 46,
        "form_builder": 55,
        "cms_builder": 62,
        "frontend_generator": 76,
        "analytics_setup": 86,
        "blog_writer": 90,
        "qa": 96,
    }
    label_by_agent = {
        "designer": "Design tokens et layout définis.",
        "copywriter": "Contenus et sections rédigés.",
        "seo": "SEO optimisé.",
        "form_builder": "Formulaire configuré.",
        "cms_builder": "Structure CMS préparée.",
        "frontend_generator": "Interface du site générée.",
        "analytics_setup": "Analytics configuré.",
        "blog_writer": "Articles de blog rédigés.",
        "qa": "Contrôle qualité finalisé.",
    }
    _append_job_event(
        job,
        {
            "step": body.agent_name,
            "label": label_by_agent.get(body.agent_name, f"Agent {body.agent_name} terminé."),
            "status": body.status,
            "progress": progress_by_agent.get(body.agent_name, 70),
        },
    )
    db.commit()
    return {"id": str(run.id)}


@router.post("/jobs/{job_id}/complete", dependencies=[Depends(require_internal)])
def complete_job(job_id: uuid.UUID, body: JobCompleteIn, db: Session = Depends(get_db)) -> dict:
    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    job.status = body.status
    job.error = body.error
    job.output = body.output
    job.tokens_in = body.tokens_in
    job.tokens_out = body.tokens_out
    job.cost_cents = body.cost_cents
    job.finished_at = datetime.now(timezone.utc)
    _append_job_event(
        job,
        {
            "step": "complete",
            "label": "Site généré avec succès"
            if body.status in (JobStatus.success, JobStatus.degraded)
            else "Génération échouée",
            "status": "ok" if body.status in (JobStatus.success, JobStatus.degraded) else "failed",
            "progress": 100,
        },
    )

    project = db.get(Project, job.project_id)
    if (
        project
        and body.status in (JobStatus.success, JobStatus.degraded)
        and job.workflow == "site_generation"
    ):
        generated_files = body.output.get("generated_files") or body.output.get("files") or []
        page_schema = dict(body.output.get("page_schema", {}) or {})
        if generated_files:
            page_schema = {
                "render_mode": "static_classic",
                "generated_files": generated_files,
                "sections": body.output.get("sections", []),
            }
        if body.output.get("form"):
            page_schema["form"] = body.output.get("form")
        if body.output.get("analytics"):
            page_schema["analytics"] = body.output.get("analytics")
        if body.output.get("articles"):
            page_schema["articles"] = body.output.get("articles")
        seo = body.output.get("seo", {})
        design_tokens = body.output.get("design_tokens", {})
        if page_schema:
            last = (
                db.query(SiteVersion)
                .filter(SiteVersion.project_id == project.id)
                .order_by(SiteVersion.version.desc())
                .first()
            )
            next_v = (last.version + 1) if last else 1
            sv = SiteVersion(
                tenant_id=project.tenant_id,
                project_id=project.id,
                version=next_v,
                page_schema=page_schema,
                seo=seo,
                design_tokens=design_tokens,
            )
            db.add(sv)
        project.design_tokens = design_tokens or project.design_tokens
        project.status = ProjectStatus.ready
    elif project and body.status in (JobStatus.failed, JobStatus.degraded):
        project.status = (
            ProjectStatus.draft if body.status == JobStatus.failed else ProjectStatus.ready
        )

    db.commit()
    return {"ok": True}


@router.post("/deployments/{deployment_id}", dependencies=[Depends(require_internal)])
def update_deployment(
    deployment_id: uuid.UUID, body: DeploymentUpdateIn, db: Session = Depends(get_db)
) -> dict:
    deployment = db.get(Deployment, deployment_id)
    if not deployment:
        raise HTTPException(404, "deployment not found")
    deployment.status = body.status
    deployment.domain = body.domain or deployment.domain
    deployment.url = body.url or deployment.url
    deployment.error = body.error
    deployment.meta = {
        **(deployment.meta or {}),
        "prefix": body.prefix,
        "upload": body.upload,
        "dns": body.dns,
        "dry_run": body.dry_run,
    }
    if body.status == DeploymentStatus.success:
        project = db.get(Project, deployment.project_id)
        if project:
            project.status = ProjectStatus.published
    db.commit()
    return {"ok": True}
