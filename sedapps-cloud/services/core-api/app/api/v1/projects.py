from __future__ import annotations

import uuid
import io
import json
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.auth.jwt import create_download_token, decode_token
from app.db.session import get_db
from app.models.membership import Membership
from app.models.ai_job import AiJob, JobStatus
from app.models.deployment import Deployment, DeploymentStatus
from app.models.project import Project, ProjectStatus
from app.models.site_version import SiteVersion
from app.schemas.project import (
    ComponentPatchIn,
    ComponentPatchOut,
    ComponentChatIn,
    DeployIn,
    DeploymentOut,
    GenerateIn,
    JobOut,
    OnboardingIn,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    ProjectChatIn,
    PageCreateIn,
    PageUpdateIn,
    PageRegenerateIn,
    DocumentReplaceIn,
    ComponentCreateIn,
)
from app.services.deploy_client import DeployClient
from app.services.credits import (
    InsufficientCreditsError,
    TOKENS_PER_CREDIT,
    release_reserved_credits,
    reserve_credits,
    settle_reserved_credits,
)
from app.services.orchestrator_client import OrchestratorClient
from app.services.ovh_client import OvhClient
from app.services.slug import unique_global_slug
from app.config import settings
from app.component_sdk import (
    apply_component_ops,
    build_component_ai_context,
    component_registry,
    migrate_page_schema,
    validate_document,
)

router = APIRouter()


def _reserve_ai_operation(db: Session, operation: str, tier: str = "standard") -> int:
    try:
        return reserve_credits(db, operation, tier)
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            {
                "code": "insufficient_ai_credits",
                "required_credits": exc.required,
                "available_credits": exc.available,
                "tokens_per_credit": TOKENS_PER_CREDIT,
            },
        ) from exc


def _settle_agent_result(db: Session, reserved: int, result: dict) -> int:
    usage = result.pop("_usage", {})
    charged = settle_reserved_credits(
        db,
        reserved,
        int(usage.get("tokens_in", 0) or 0),
        int(usage.get("tokens_out", 0) or 0),
    )
    db.commit()
    return charged


@router.get("/components/sdk", tags=["components"])
def list_component_sdk() -> dict:
    return {
        "sdk_version": "1.0.0",
        "components": {name: manifest.model_dump() for name, manifest in component_registry.items()},
    }


@router.get("/check-domain/verify")
def check_domain_availability(
    domain: str,
    db: Session = Depends(get_current_org_db),
) -> dict[str, bool]:
    if not domain or not domain.strip():
        return {"available": True}
    return {"available": OvhClient().is_domain_available(domain.strip().lower())}


def _get_owned_project(db: Session, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if not project or project.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return project


def _site_versions(db: Session, project_id: uuid.UUID) -> list[SiteVersion]:
    return (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project_id)
        .order_by(SiteVersion.version.desc())
        .all()
    )


def _component_tree(version: SiteVersion) -> dict:
    schema = dict(version.page_schema or {})
    tree = schema.get("component_tree")
    if isinstance(tree, dict):
        return tree
    return migrate_page_schema(schema, version.design_tokens or {})


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


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_current_org_db),
) -> ProjectOut:
    project = _get_owned_project(db, project_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=204, response_class=Response)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> Response:
    project = _get_owned_project(db, project_id)
    db.delete(project)
    db.commit()
    return Response(status_code=204)


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


@router.get("/{project_id}/plan")
def get_project_plan(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    job = (
        db.query(AiJob)
        .filter(AiJob.project_id == project.id)
        .order_by(AiJob.created_at.desc())
        .first()
    )
    events = list((job.input or {}).get("events") or []) if job else []
    return {
        "title": f"Plan de création — {project.name}",
        "status": job.status.value if job else "draft",
        "phases": events,
        "brief": project.brief,
    }


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

    tier = "premium" if project.brief.get("premium") else "standard"
    try:
        reserved_credits = reserve_credits(db, "site_generation", tier)
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            {
                "code": "insufficient_ai_credits",
                "required_credits": exc.required,
                "available_credits": exc.available,
                "tokens_per_credit": TOKENS_PER_CREDIT,
            },
        ) from exc

    previous_status = project.status
    job = AiJob(
        tenant_id=db.info["tenant_id"],
        project_id=project.id,
        workflow="site_generation",
        status=JobStatus.queued,
        input={"brief": project.brief, "locale": body.locale},
        reserved_credits=reserved_credits,
    )
    project.status = ProjectStatus.generating
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        client = OrchestratorClient()
        await client.enqueue_site_generation(
            job_id=str(job.id),
            project_id=str(project.id),
            tenant_id=str(project.tenant_id),
            brief=project.brief,
            locale=body.locale,
        )
    except Exception as exc:
        job.status = JobStatus.failed
        job.error = "AI orchestrator unavailable"
        job.finished_at = datetime.now(timezone.utc)
        release_reserved_credits(db, reserved_credits)
        job.credits_settled = True
        project.status = previous_status
        db.commit()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "AI orchestrator unavailable"
        ) from exc
    return JobOut(id=str(job.id), status=job.status.value, workflow=job.workflow)


@router.get("/{project_id}/components/{component_id}/ai-context", tags=["components"])
def component_ai_context(
    project_id: uuid.UUID,
    component_id: str,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    version = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")
    tree = _component_tree(version)
    try:
        return build_component_ai_context(tree, component_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/{project_id}/document", tags=["components"])
def project_document(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    versions = _site_versions(db, project.id)
    if not versions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")
    return {
        "site_version_id": str(versions[0].id),
        "version": versions[0].version,
        "document": _component_tree(versions[0]),
    }


def _save_document_version(db: Session, project: Project, current: SiteVersion, tree: dict, action: str) -> SiteVersion:
    validate_document(tree)
    schema = dict(current.page_schema or {})
    schema["component_tree"] = tree
    schema["_sdk_revision"] = {
        "action": action,
        "parent_site_version_id": str(current.id),
    }
    created = SiteVersion(
        tenant_id=project.tenant_id,
        project_id=project.id,
        version=current.version + 1,
        page_schema=schema,
        seo=current.seo,
        design_tokens=current.design_tokens,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def _page_template(page_id: str, slug: str, name: str, template: str) -> dict:
    content = [] if template == "blank" else [
        {"id": f"{page_id}-title", "type": "Title", "props": {"text": name, "level": "h1"}},
        {"id": f"{page_id}-text", "type": "Text", "props": {"text": f"Présentez ici le contenu de la page {name}."}},
    ]
    if template == "contact":
        content.append({"id": f"{page_id}-button", "type": "Button", "props": {"label": "Nous contacter", "variant": "primary", "href": "mailto:contact@example.com", "disabled": False}})
    if not content:
        content = [{"id": f"{page_id}-text", "type": "Text", "props": {"text": "Commencez à écrire ici."}}]
    return {
        "id": page_id,
        "type": "Page",
        "props": {"slug": slug},
        "slots": {"body": [{
            "id": f"{page_id}-section",
            "type": "Section",
            "props": {"variant": "default"},
            "slots": {"content": content},
        }]},
    }


@router.post("/{project_id}/pages", tags=["components"], status_code=201)
def create_page(project_id: uuid.UUID, body: PageCreateIn, db: Session = Depends(get_current_org_db)) -> dict:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    tree = _component_tree(current)
    if any(page.get("props", {}).get("slug") == body.slug for page in tree.get("pages", [])):
        raise HTTPException(status.HTTP_409_CONFLICT, "page slug already exists")
    page_id = f"page-{body.slug}"
    tree.setdefault("pages", []).append(_page_template(page_id, body.slug, body.name, body.template))
    created = _save_document_version(db, project, current, tree, "create_page")
    return {"page": tree["pages"][-1], "version": created.version, "undo_depth": len(_site_versions(db, project.id))}


@router.post("/{project_id}/pages/{page_id}/components", tags=["components"], status_code=201)
def create_page_component(project_id: uuid.UUID, page_id: str, body: ComponentCreateIn, db: Session = Depends(get_current_org_db)) -> dict:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    tree = _component_tree(current)
    page = next((item for item in tree.get("pages", []) if item.get("id") == page_id), None)
    if not page:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "page not found")
    defaults = {
        "Title": {"text": "Nouveau titre", "level": "h2"},
        "Text": {"text": "Ajoutez votre texte ici."},
        "Button": {"label": "En savoir plus", "variant": "primary", "href": "#", "disabled": False},
        "Image": {"src": "https://images.unsplash.com/photo-1497366754035-f200968a6e72", "alt": "Nouvelle image"},
        "Section": {"variant": "default"},
    }
    component_id = f"{page_id}-{body.type.lower()}-{uuid.uuid4().hex[:8]}"
    component = {"id": component_id, "type": body.type, "props": {**defaults[body.type], **body.props}}
    if body.type == "Section":
        component["slots"] = {"content": [{"id": f"{component_id}-text", "type": "Text", "props": {"text": "Nouvelle section"}}]}
        page.setdefault("slots", {}).setdefault("body", []).append(component)
    else:
        body_sections = page.setdefault("slots", {}).setdefault("body", [])
        if not body_sections:
            body_sections.append({"id": f"{page_id}-section", "type": "Section", "props": {"variant": "default"}, "slots": {"content": []}})
        body_sections[-1].setdefault("slots", {}).setdefault("content", []).append(component)
    created = _save_document_version(db, project, current, tree, "create_component")
    return {"component": component, "version": created.version, "can_undo": True}


@router.patch("/{project_id}/pages/{page_id}", tags=["components"])
def update_page(project_id: uuid.UUID, page_id: str, body: PageUpdateIn, db: Session = Depends(get_current_org_db)) -> dict:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    tree = _component_tree(current)
    page = next((item for item in tree.get("pages", []) if item.get("id") == page_id), None)
    if not page:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "page not found")
    if body.slug:
        if any(item.get("id") != page_id and item.get("props", {}).get("slug") == body.slug for item in tree.get("pages", [])):
            raise HTTPException(status.HTTP_409_CONFLICT, "page slug already exists")
        page.setdefault("props", {})["slug"] = body.slug
    if body.name:
        for section in page.get("slots", {}).get("body", []):
            for item in section.get("slots", {}).get("content", []):
                if item.get("type") == "Title":
                    item.setdefault("props", {})["text"] = body.name
                    break
    created = _save_document_version(db, project, current, tree, "update_page")
    return {"page": page, "version": created.version}


@router.delete("/{project_id}/pages/{page_id}", tags=["components"], status_code=204)
def delete_page(project_id: uuid.UUID, page_id: str, db: Session = Depends(get_current_org_db)) -> Response:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    tree = _component_tree(current)
    pages = tree.get("pages", [])
    if len(pages) <= 1:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "a website must keep one page")
    tree["pages"] = [page for page in pages if page.get("id") != page_id]
    if len(tree["pages"]) == len(pages):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "page not found")
    _save_document_version(db, project, current, tree, "delete_page")
    return Response(status_code=204)


@router.post("/{project_id}/pages/{page_id}/regenerate", tags=["components"])
def regenerate_page(project_id: uuid.UUID, page_id: str, body: PageRegenerateIn, db: Session = Depends(get_current_org_db)) -> dict:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    tree = _component_tree(current)
    index = next((i for i, item in enumerate(tree.get("pages", [])) if item.get("id") == page_id), None)
    if index is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "page not found")
    old = tree["pages"][index]
    slug = old.get("props", {}).get("slug", "page")
    name = slug.replace("-", " ").title()
    page = _page_template(page_id, slug, name, "standard")
    page["slots"]["body"][0]["slots"]["content"][1]["props"]["text"] = body.instruction
    tree["pages"][index] = page
    created = _save_document_version(db, project, current, tree, "regenerate_page")
    return {"page": page, "version": created.version, "can_undo": True}


@router.put("/{project_id}/document", tags=["components"])
def replace_project_document(project_id: uuid.UUID, body: DocumentReplaceIn, db: Session = Depends(get_current_org_db)) -> dict:
    project = _get_owned_project(db, project_id)
    current = _site_versions(db, project.id)[0]
    try:
        created = _save_document_version(db, project, current, body.document, "code_edit")
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return {"status": "ok", "version": created.version, "site_version_id": str(created.id), "can_undo": True}


@router.post("/{project_id}/edit_chat", tags=["components"])
async def edit_component_chat(
    project_id: uuid.UUID,
    body: ComponentChatIn,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    versions = _site_versions(db, project.id)
    if not versions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")
    tree = _component_tree(versions[0])
    reserved_credits = _reserve_ai_operation(db, "site_edit")
    db.commit()
    credits_settled = False
    try:
        context = build_component_ai_context(tree, body.element_id)
        result = await OrchestratorClient().run_agent(
            "component_editor",
            project_id=str(project.id),
            tenant_id=str(project.tenant_id),
            context=context,
            params={"instruction": body.instruction},
        )
        charged_credits = _settle_agent_result(db, reserved_credits, result)
        credits_settled = True
        ops = result.get("ops") or []
        patched = patch_component(
            project_id,
            ComponentPatchIn(element_id=body.element_id, ops=ops),
            db,
        )
    except HTTPException:
        if not credits_settled:
            release_reserved_credits(db, reserved_credits)
            db.commit()
        raise
    except ValueError as exc:
        if not credits_settled:
            release_reserved_credits(db, reserved_credits)
            db.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except Exception as exc:
        if not credits_settled:
            release_reserved_credits(db, reserved_credits)
            db.commit()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI editor unavailable") from exc
    return {
        **patched.model_dump(),
        "ops": ops,
        "message": result.get("message") or "Modification appliquée.",
        "charged_credits": charged_credits,
    }


@router.post("/{project_id}/chat", tags=["ai"])
async def project_chat(
    project_id: uuid.UUID,
    body: ProjectChatIn,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    versions = _site_versions(db, project.id)
    context = {
        "name": project.name,
        "sector": project.sector,
        "brief": project.brief,
        "design_system": _component_tree(versions[0]).get("design_system", {}) if versions else {},
    }
    reserved_credits = _reserve_ai_operation(db, "site_edit")
    db.commit()
    try:
        result = await OrchestratorClient().run_agent(
            "project_chat",
            project_id=str(project.id),
            tenant_id=str(project.tenant_id),
            context=context,
            params={"messages": body.messages},
        )
        charged_credits = _settle_agent_result(db, reserved_credits, result)
        result["charged_credits"] = charged_credits
        return result
    except Exception as exc:
        release_reserved_credits(db, reserved_credits)
        db.commit()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI chat unavailable") from exc


@router.post(
    "/{project_id}/patch_element",
    response_model=ComponentPatchOut,
    tags=["components"],
)
def patch_component(
    project_id: uuid.UUID,
    body: ComponentPatchIn,
    db: Session = Depends(get_current_org_db),
) -> ComponentPatchOut:
    project = _get_owned_project(db, project_id)
    versions = _site_versions(db, project.id)
    if not versions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")
    current = versions[0]
    try:
        tree, element = apply_component_ops(_component_tree(current), body.element_id, body.ops)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if "not found" in message else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(code, message) from exc

    schema = dict(current.page_schema or {})
    schema["component_tree"] = tree
    schema["_sdk_revision"] = {
        "action": "edit",
        "component_id": body.element_id,
        "parent_site_version_id": str(current.id),
        "operations": body.ops,
    }
    created = SiteVersion(
        tenant_id=project.tenant_id,
        project_id=project.id,
        version=current.version + 1,
        page_schema=schema,
        seo=current.seo,
        design_tokens=current.design_tokens,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return ComponentPatchOut(
        element=element,
        site_version_id=str(created.id),
        version=created.version,
        can_undo=True,
        undo_depth=len(versions),
    )


@router.post("/{project_id}/undo", tags=["components"])
def undo_component_edit(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict:
    project = _get_owned_project(db, project_id)
    versions = _site_versions(db, project.id)
    if len(versions) < 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "rien à annuler")
    current = versions[0]
    revision = (current.page_schema or {}).get("_sdk_revision") or {}
    parent_id = revision.get("parent_site_version_id")
    if revision.get("action") == "undo" and not parent_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "rien à annuler")
    target = db.get(SiteVersion, uuid.UUID(parent_id)) if parent_id else versions[1]
    if not target or target.project_id != project.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "historique invalide")

    target_schema = dict(target.page_schema or {})
    target_revision = target_schema.get("_sdk_revision") or {}
    restored_schema = dict(target_schema)
    restored_schema["_sdk_revision"] = {
        "action": "undo",
        "restored_site_version_id": str(target.id),
        "parent_site_version_id": target_revision.get("parent_site_version_id"),
    }
    restored = SiteVersion(
        tenant_id=project.tenant_id,
        project_id=project.id,
        version=current.version + 1,
        page_schema=restored_schema,
        seo=target.seo,
        design_tokens=target.design_tokens,
    )
    db.add(restored)
    db.commit()
    db.refresh(restored)
    return {
        "status": "ok",
        "site_version_id": str(restored.id),
        "version": restored.version,
        "component_tree": _component_tree(restored),
        "can_undo": bool(target_revision.get("parent_site_version_id")),
        "undo_depth": 1 if target_revision.get("parent_site_version_id") else 0,
    }


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
                "baseUrl": body.custom_domain
                or f"https://{project.slug}.{settings.DEPLOY_BASE_DOMAIN}",
            },
        }
    else:
        payload = {
            "site": {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "locale": project.brief.get("locale", "fr"),
                "baseUrl": body.custom_domain
                or f"https://{project.slug}.{settings.DEPLOY_BASE_DOMAIN}",
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
        domain=body.custom_domain or f"{project.slug}.{settings.DEPLOY_BASE_DOMAIN}",
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


@router.get("/{project_id}/deployments/{deployment_id}", response_model=DeploymentOut)
def get_deployment(
    project_id: uuid.UUID,
    deployment_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> DeploymentOut:
    project = _get_owned_project(db, project_id)
    deployment = db.get(Deployment, deployment_id)
    if not deployment or deployment.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "deployment not found")
    return DeploymentOut(
        id=str(deployment.id),
        status=deployment.status.value,
        domain=deployment.domain,
        url=deployment.url,
        error=deployment.error,
    )


@router.get("/{project_id}/download")
def download_project(
    project_id: uuid.UUID,
    token: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload["sub"])
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    if (
        payload.get("type") != "download"
        or payload.get("scope") != "project:download"
        or payload.get("project") != str(project_id)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid download ticket")
    membership = db.query(Membership).filter(Membership.user_id == user_id).first()
    project = db.get(Project, project_id)
    if (
        not membership
        or payload.get("org") != str(membership.org_id)
        or not project
        or project.tenant_id != membership.org_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    version = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site version not found")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        files = (version.page_schema or {}).get("generated_files") or []
        for item in files:
            if isinstance(item, dict) and item.get("path") and isinstance(item.get("content"), str):
                archive.writestr(str(item["path"]).lstrip("/"), item["content"])
        archive.writestr(
            "sala-ai/component-tree.json",
            json.dumps(_component_tree(version), ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "sala-ai/design-tokens.json",
            json.dumps(version.design_tokens or {}, ensure_ascii=False, indent=2),
        )
    buffer.seek(0)
    filename = f"{project.slug}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{project_id}/download-ticket")
def create_project_download_ticket(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> dict[str, str | int]:
    project = _get_owned_project(db, project_id)
    token = create_download_token(
        str(db.info["user_id"]),
        str(project.tenant_id),
        str(project.id),
    )
    return {
        "path": f"/v1/projects/{project.id}/download?token={token}",
        "expires_in_seconds": 120,
    }
