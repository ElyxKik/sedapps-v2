from __future__ import annotations

import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.config import settings
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
    ProjectUpdate,
    RollbackIn,
    SiteVersionOut,
)
from app.services.deploy_client import DeployClient
from app.services.orchestrator_client import OrchestratorClient
from app.services.ovh_client import OvhClient
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
    # Get active jobs to populate active_job_id
    active_jobs = (
        db.query(AiJob)
        .filter(
            AiJob.tenant_id == db.info["tenant_id"],
            AiJob.status.in_([JobStatus.queued, JobStatus.running]),
        )
        .order_by(AiJob.created_at.asc())
        .all()
    )
    project_to_job = {job.project_id: job.id for job in active_jobs}

    res = []
    for r in rows:
        p_out = ProjectOut.model_validate(r)
        p_out.active_job_id = project_to_job.get(r.id)
        res.append(p_out)
    return res


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
    project = _get_owned_project(db, project_id)
    active_job = (
        db.query(AiJob)
        .filter(
            AiJob.project_id == project.id, AiJob.status.in_([JobStatus.queued, JobStatus.running])
        )
        .order_by(AiJob.created_at.desc())
        .first()
    )
    p_out = ProjectOut.model_validate(project)
    p_out.active_job_id = active_job.id if active_job else None
    return p_out


@router.delete("/{project_id}", status_code=204, response_class=Response)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> Response:
    project = _get_owned_project(db, project_id)
    db.delete(project)
    db.commit()
    return Response(status_code=204)


@router.get("/check-domain/verify")
def check_domain_availability(
    domain: str,
    db: Session = Depends(get_current_org_db),
) -> dict[str, bool]:
    """
    Check if a domain is available via the OVH API.
    Returns: {"available": true|false}
    """
    if not domain or not domain.strip():
        return {"available": True}

    client = OvhClient()
    available = client.is_domain_available(domain.strip().lower())
    return {"available": available}


@router.post("/{project_id}/onboarding", response_model=ProjectOut)
def save_onboarding(
    project_id: uuid.UUID,
    body: OnboardingIn,
    db: Session = Depends(get_current_org_db),
) -> ProjectOut:
    project = _get_owned_project(db, project_id)
    project.brief = body.model_dump()
    project.sector = body.sector or project.sector
    project.custom_domain = body.custom_domain or project.custom_domain
    db.commit()
    db.refresh(project)

    active_job = (
        db.query(AiJob)
        .filter(
            AiJob.project_id == project.id, AiJob.status.in_([JobStatus.queued, JobStatus.running])
        )
        .order_by(AiJob.created_at.desc())
        .first()
    )
    p_out = ProjectOut.model_validate(project)
    p_out.active_job_id = active_job.id if active_job else None
    return p_out


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

    if site_version.page_schema.get("render_mode") == "static_classic":
        payload = {
            "render_mode": "static_classic",
            "files": site_version.page_schema.get("generated_files", []),
            "site": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "locale": project.brief.get("locale", "fr"),
                "baseUrl": body.custom_domain or f"https://{project.slug}.sedapps.cloud",
            },
        }
    else:
        payload = {
            "site": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "locale": project.brief.get("locale", "fr"),
                "baseUrl": body.custom_domain or f"https://{project.slug}.sedapps.cloud",
            },
            "page_schema": site_version.page_schema,
            "design_tokens": site_version.design_tokens,
            "seo": site_version.seo,
            "form": site_version.page_schema.get("form", {}),
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

    # Mark the site version as published
    site_version.is_published = True
    site_version.published_at = datetime.now(timezone.utc)

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
        site_version_id=str(site_version.id),
        created_at=deployment.created_at,
    )


# ── Site versions & deployments ─────────────────────────────────────────────

@router.get("/{project_id}/versions", response_model=list[SiteVersionOut], tags=["projects"])
def list_site_versions(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> list[SiteVersionOut]:
    project = _get_owned_project(db, project_id)
    versions = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .all()
    )
    return [
        SiteVersionOut(
            id=str(v.id),
            version=v.version,
            label=v.label,
            is_published=v.is_published,
            published_at=v.published_at,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/{project_id}/deployments", response_model=list[DeploymentOut], tags=["projects"])
def list_deployments(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> list[DeploymentOut]:
    project = _get_owned_project(db, project_id)
    deployments = (
        db.query(Deployment)
        .filter(Deployment.project_id == project.id)
        .order_by(Deployment.created_at.desc())
        .all()
    )
    return [
        DeploymentOut(
            id=str(d.id),
            status=d.status.value,
            domain=d.domain,
            url=d.url,
            error=d.error,
            site_version_id=str(d.site_version_id),
            created_at=d.created_at,
        )
        for d in deployments
    ]


@router.post("/{project_id}/rollback", response_model=DeploymentOut, status_code=202, tags=["projects"])
async def rollback_to_version(
    project_id: uuid.UUID,
    body: RollbackIn,
    db: Session = Depends(get_current_org_db),
) -> DeploymentOut:
    project = _get_owned_project(db, project_id)
    target = db.get(SiteVersion, uuid.UUID(body.site_version_id))
    if not target or target.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")

    if target.page_schema.get("render_mode") == "static_classic":
        payload = {
            "render_mode": "static_classic",
            "files": target.page_schema.get("generated_files", []),
            "site": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "locale": project.brief.get("locale", "fr"),
                "baseUrl": body.custom_domain or f"https://{project.slug}.sedapps.cloud",
            },
        }
    else:
        payload = {
            "site": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "locale": project.brief.get("locale", "fr"),
                "baseUrl": body.custom_domain or f"https://{project.slug}.sedapps.cloud",
            },
            "page_schema": target.page_schema,
            "design_tokens": target.design_tokens,
            "seo": target.seo,
            "form": target.page_schema.get("form", {}),
            "analytics": target.page_schema.get("analytics", {}),
            "articles": target.page_schema.get("articles", []),
        }

    deployment = Deployment(
        tenant_id=db.info["tenant_id"],
        project_id=project.id,
        site_version_id=target.id,
        status=DeploymentStatus.queued,
        domain=body.custom_domain or f"{project.slug}.sedapps.cloud",
    )
    db.add(deployment)

    for v in db.query(SiteVersion).filter(SiteVersion.project_id == project.id).all():
        v.is_published = v.id == target.id
    target.is_published = True
    target.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(deployment)

    client = DeployClient()
    await client.enqueue_site_deployment(
        deployment_id=str(deployment.id),
        tenant_id=str(project.tenant_id),
        project_id=str(project.id),
        site_version_id=str(target.id),
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
        site_version_id=str(target.id),
        created_at=deployment.created_at,
    )


# ── Project update ───────────────────────────────────────────────────────────

@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_current_org_db),
) -> ProjectOut:
    project = _get_owned_project(db, project_id)
    if body.name is not None:
        project.name = body.name
    if body.sector is not None:
        project.sector = body.sector
    if body.design_tokens is not None:
        project.design_tokens = body.design_tokens
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


# ── Chat with project ────────────────────────────────────────────────────────

@router.post("/{project_id}/chat", tags=["projects"])
def chat_with_project(
    project_id: uuid.UUID,
    body: dict[str, Any],
    db: Session = Depends(get_current_org_db),
) -> dict[str, str]:
    project = _get_owned_project(db, project_id)
    messages_in = body.get("messages") or []
    if not isinstance(messages_in, list) or not messages_in:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "messages required")

    brief = project.brief or {}
    tokens = project.design_tokens or {}
    system_prompt = (
        "Tu es un assistant IA expert en création de sites web pour la plateforme SedApps. "
        "Tu aides l'utilisateur à itérer sur son site déjà généré. Reste concret, concis, en français. "
        f"Contexte projet : nom={project.name}, secteur={project.sector or ''}. "
        f"Brief onboarding : {json.dumps(brief, ensure_ascii=False)}. "
        f"Design tokens : {json.dumps(tokens, ensure_ascii=False)}. "
        "Si l'utilisateur demande une modification (couleur, texte, section), explique précisément ce que tu ferais "
        "et propose un texte ou une valeur prête à appliquer. Pas de markdown lourd."
    )

    if not settings.deepseek_api_key:
        last_user = next((m.get("text", "") for m in reversed(messages_in) if m.get("role") == "user"), "")
        return {"message": f"(mode local sans clé DeepSeek) J'ai bien noté ta demande : « {last_user} ». Configure DEEPSEEK_API_KEY pour des réponses IA réelles."}

    payload_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages_in[-12:]:
        role = msg.get("role")
        text = msg.get("text") or msg.get("content") or ""
        if role not in {"user", "assistant"} or not text:
            continue
        payload_messages.append({"role": role, "content": text})

    try:
        response = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
            json={"model": settings.deepseek_model, "messages": payload_messages, "temperature": 0.6},
            timeout=60,
        )
        if response.status_code >= 400:
            detail = response.text[:800]
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"DeepSeek HTTP {response.status_code}: {detail}")
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"DeepSeek error: {type(exc).__name__}: {exc}") from exc

    return {"message": content}


# ── Project plan ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/plan", tags=["projects"])
def get_project_plan(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict[str, Any]:
    project = _get_owned_project(db, project_id)
    brief = project.brief or {}
    if not brief:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No brief available")

    business = brief.get("business_name") or project.name
    sector = brief.get("sector") or project.sector or "Services"

    return {
        "title": f"Plan de création du site {business}",
        "phases": [
            {
                "phase": "Analyse & Design",
                "duration": "2-3 jours",
                "tasks": [
                    {"id": "task-1", "title": "Analyse du brief", "status": "pending", "priority": "high"},
                    {"id": "task-2", "title": "Création de la palette de couleurs", "status": "pending", "priority": "high"},
                    {"id": "task-3", "title": "Wireframes des pages principales", "status": "pending", "priority": "high"},
                ],
            },
            {
                "phase": "Contenu & Rédaction",
                "duration": "3-4 jours",
                "tasks": [
                    {"id": "task-4", "title": "Rédaction du hero et CTA", "status": "pending", "priority": "high"},
                    {"id": "task-5", "title": f"Développement des sections {sector}", "status": "pending", "priority": "high"},
                    {"id": "task-6", "title": "Optimisation SEO", "status": "pending", "priority": "medium"},
                ],
            },
            {
                "phase": "Développement",
                "duration": "4-5 jours",
                "tasks": [
                    {"id": "task-7", "title": "Développement HTML/CSS", "status": "pending", "priority": "high"},
                    {"id": "task-8", "title": "Intégration JavaScript", "status": "pending", "priority": "high"},
                    {"id": "task-9", "title": "Tests responsivité", "status": "pending", "priority": "high"},
                ],
            },
            {
                "phase": "Revue & Déploiement",
                "duration": "1-2 jours",
                "tasks": [
                    {"id": "task-10", "title": "Revue qualité", "status": "pending", "priority": "high"},
                    {"id": "task-11", "title": "Optimisation performance", "status": "pending", "priority": "medium"},
                    {"id": "task-12", "title": "Déploiement en production", "status": "pending", "priority": "high"},
                ],
            },
        ],
        "timeline": "10-14 jours",
        "team": ["Designer", "Copywriter", "Frontend Developer", "SEO Specialist", "QA"],
        "deliverables": [
            "Design system complet",
            "Contenu optimisé",
            "Site responsive",
            "Rapports SEO",
            "Documentation",
        ],
    }


# ── Download project as ZIP ──────────────────────────────────────────────────

@router.get("/{project_id}/download", tags=["projects"])
def download_project_zip(
    project_id: uuid.UUID,
    token: str = Query(...),
    db: Session = Depends(get_current_org_db),
) -> StreamingResponse:
    project = _get_owned_project(db, project_id)
    site_version = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not site_version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no site version available")

    page_schema = site_version.page_schema or {}
    files = page_schema.get("generated_files") or page_schema.get("files") or []
    if not files:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no generated files available")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in files:
            path = str(item.get("path") or "").strip().lstrip("/")
            content = str(item.get("content") or "")
            if path and ".." not in path.split("/"):
                zip_file.writestr(path, content)
    archive.seek(0)
    filename = f"{project.slug}-{project.id}.zip"
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Element editor: patch, undo, edit_chat ───────────────────────────────────

_UNDO_STACKS: dict[str, list[tuple[str, str]]] = {}
_UNDO_LIMIT = 30


def _push_undo(project_id: str, filename: str, html_str: str) -> None:
    stack = _UNDO_STACKS.setdefault(project_id, [])
    stack.append((filename, html_str))
    if len(stack) > _UNDO_LIMIT:
        del stack[: len(stack) - _UNDO_LIMIT]


def _latest_site_files(db: Session, project: Project) -> list[dict[str, Any]]:
    sv = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not sv:
        return []
    page_schema = sv.page_schema or {}
    return list(page_schema.get("generated_files") or page_schema.get("files") or [])


def _save_site_files(db: Session, project: Project, files: list[dict[str, Any]]) -> None:
    sv = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not sv:
        return
    page_schema = dict(sv.page_schema or {})
    page_schema["generated_files"] = files
    sv.page_schema = page_schema
    db.commit()


@router.post("/{project_id}/patch_element", tags=["projects"])
def patch_element(
    project_id: uuid.UUID,
    body: dict[str, Any],
    db: Session = Depends(get_current_org_db),
) -> dict[str, Any]:
    from app.site_editor import apply_ops

    project = _get_owned_project(db, project_id)
    element_id = body.get("element_id")
    ops = body.get("ops") or []
    filename = body.get("filename") or "index.html"
    if not element_id or not isinstance(ops, list):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "element_id and ops required")

    files = _latest_site_files(db, project)
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == filename), -1)
    if idx < 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{filename} not found")

    current_html = files[idx].get("content", "")
    try:
        new_html, summary = apply_ops(current_html, element_id, ops)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    _push_undo(str(project.id), filename, current_html)
    files[idx] = {**files[idx], "content": new_html}
    _save_site_files(db, project, files)
    return {"status": "ok", "element": summary, "can_undo": True, "undo_depth": len(_UNDO_STACKS.get(str(project.id), []))}


@router.post("/{project_id}/undo", tags=["projects"])
def undo_last_edit(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict[str, Any]:
    project = _get_owned_project(db, project_id)
    stack = _UNDO_STACKS.get(str(project.id)) or []
    if not stack:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "rien à annuler")

    filename, previous = stack.pop()
    files = _latest_site_files(db, project)
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == filename), -1)
    if idx < 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{filename} not found")

    files[idx] = {**files[idx], "content": previous}
    _save_site_files(db, project, files)
    return {"status": "ok", "undo_depth": len(stack)}


@router.post("/{project_id}/edit_chat", tags=["projects"])
def edit_chat(
    project_id: uuid.UUID,
    body: dict[str, Any],
    db: Session = Depends(get_current_org_db),
) -> dict[str, Any]:
    from app.site_editor import apply_ops

    project = _get_owned_project(db, project_id)
    element_id = body.get("element_id")
    instruction = (body.get("instruction") or "").strip()
    selected = body.get("selected") or {}
    if not element_id or not instruction:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "element_id and instruction required")

    if not settings.deepseek_api_key:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "DEEPSEEK_API_KEY non configurée")

    system_prompt = (
        "Tu es un éditeur visuel de site web. L'utilisateur a sélectionné un élément HTML "
        "et te demande une modification ciblée. Réponds UNIQUEMENT par un JSON: "
        '{"ops":[{"op":"set_text","value":"..."},'
        '{"op":"set_attr","name":"src","value":"..."},'
        '{"op":"set_style","name":"background-color","value":"#0ea5e9"}]}. '
        "Utilise des couleurs CSS valides (hex, rgb, named). N'invente pas d'autres ops. "
        "Si plusieurs changements demandés, mets-les tous dans ops."
    )
    user_payload = {
        "instruction": instruction,
        "selected": {
            "id": element_id,
            "tag": selected.get("tag"),
            "text": selected.get("text"),
            "src": selected.get("src"),
            "classes": selected.get("classes"),
        },
    }
    try:
        response = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "max_tokens": 1000,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        ops = parsed.get("ops") or []
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"DeepSeek error: {exc}") from exc

    files = _latest_site_files(db, project)
    filename = body.get("filename") or "index.html"
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == filename), -1)
    if idx < 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{filename} not found")

    current_html = files[idx].get("content", "")
    try:
        new_html, summary = apply_ops(current_html, element_id, ops)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    _push_undo(str(project.id), filename, current_html)
    files[idx] = {**files[idx], "content": new_html}
    _save_site_files(db, project, files)
    return {"status": "ok", "ops": ops, "element": summary, "undo_depth": len(_UNDO_STACKS.get(str(project.id), []))}
