from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.ai_job import AiJob, JobStatus
from app.models.deployment import Deployment, DeploymentStatus
from app.models.project import Project, ProjectStatus
from app.models.site_version import SiteVersion
from app.schemas.project import (
    DeployIn,
    DeploymentOut,
    GenerateIn,
    JobOut,
    OnboardingIn,
    ProjectCreate,
    ProjectOut,
)
from app.services.deploy_client import DeployClient
from app.services.orchestrator_client import OrchestratorClient
from app.services.slug import unique_global_slug

router = APIRouter()


def _get_owned_project(db: Session, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if not project or project.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_current_org_db)) -> list[ProjectOut]:
    rows = (
        db.query(Project)
        .filter(Project.tenant_id == db.info["tenant_id"])
        .order_by(Project.created_at.desc())
        .all()
    )
    return [ProjectOut.model_validate(r) for r in rows]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_current_org_db)) -> ProjectOut:
    slug = unique_global_slug(db, Project, body.name)
    project = Project(
        tenant_id=db.info["tenant_id"],
        name=body.name,
        slug=slug,
        sector=body.sector,
        status=ProjectStatus.draft,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> ProjectOut:
    return ProjectOut.model_validate(_get_owned_project(db, project_id))


@router.post("/{project_id}/onboarding", response_model=ProjectOut)
def save_onboarding(
    project_id: uuid.UUID,
    body: OnboardingIn,
    db: Session = Depends(get_current_org_db),
) -> ProjectOut:
    project = _get_owned_project(db, project_id)
    project.brief = body.model_dump()
    project.sector = body.sector or project.sector
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.post("/{project_id}/generate", response_model=JobOut, status_code=202)
async def generate_site(
    project_id: uuid.UUID,
    body: GenerateIn,
    db: Session = Depends(get_current_org_db),
) -> JobOut:
    project = _get_owned_project(db, project_id)
    if project.status == ProjectStatus.generating and not body.force:
        raise HTTPException(status.HTTP_409_CONFLICT, "already generating")
    if not project.brief:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "complete onboarding first")

    job = AiJob(
        tenant_id=db.info["tenant_id"],
        project_id=project.id,
        workflow="site_generation",
        status=JobStatus.queued,
        input={"brief": project.brief, "locale": body.locale},
    )
    project.status = ProjectStatus.generating
    db.add(job)
    db.commit()
    db.refresh(job)

    client = OrchestratorClient()
    await client.enqueue_site_generation(
        job_id=str(job.id),
        project_id=str(project.id),
        tenant_id=str(project.tenant_id),
        brief=project.brief,
        locale=body.locale,
    )
    return JobOut(id=str(job.id), status=job.status.value, workflow=job.workflow)


@router.post("/{project_id}/deploy", response_model=DeploymentOut, status_code=202)
async def deploy_project(
    project_id: uuid.UUID,
    body: DeployIn,
    db: Session = Depends(get_current_org_db),
) -> DeploymentOut:
    project = _get_owned_project(db, project_id)
    query = db.query(SiteVersion).filter(SiteVersion.project_id == project.id)
    if body.site_version_id:
        site_version = query.filter(SiteVersion.id == uuid.UUID(body.site_version_id)).first()
    else:
        site_version = query.order_by(SiteVersion.version.desc()).first()
    if not site_version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")

    payload = {
        "site": {
            "id": str(project.id),
            "name": project.name,
            "slug": project.slug,
            "locale": project.brief.get("locale", "fr"),
            "baseUrl": body.custom_domain or f"https://{project.slug}.sedapps.cloud",
        },
        "designTokens": site_version.design_tokens,
        "pages": site_version.page_schema.get("pages", site_version.page_schema),
        "seo": site_version.seo,
        "forms": site_version.page_schema.get("forms", []),
        "analytics": site_version.page_schema.get("analytics", {}),
        "articles": site_version.page_schema.get("articles", []),
    }
    deployment = Deployment(
        tenant_id=db.info["tenant_id"],
        project_id=project.id,
        site_version_id=site_version.id,
        status=DeploymentStatus.queued,
        domain=body.custom_domain or f"{project.slug}.sedapps.cloud",
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    client = DeployClient()
    await client.enqueue_site_deployment(
        deployment_id=str(deployment.id),
        tenant_id=str(project.tenant_id),
        project_id=str(project.id),
        site_version_id=str(site_version.id),
        slug=project.slug,
        custom_domain=body.custom_domain,
        payload=payload,
    )
    return DeploymentOut(
        id=str(deployment.id),
        status=deployment.status.value,
        domain=deployment.domain,
        url=deployment.url,
        error=deployment.error,
    )
