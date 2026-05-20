from __future__ import annotations

import asyncio
import json as _json
import mimetypes
import secrets
import uuid
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, StreamingResponse
from jose import JWTError, jwt
from sqlalchemy import text as _sa_text
from sqlalchemy.orm import Session

from app.llm_site_generator import generate_llm_site_payload, generate_project_plan, generate_site_single_shot
from app.config import settings
from app.database import Base, engine, get_db
from app.models import AiJob, Article, Comment, FormSubmission, MediaAsset, Project, User
from app.schemas import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    CommentIn,
    CommentOut,
    CommentUpdate,
    DeployIn,
    DeploymentOut,
    FormSubmissionIn,
    FormSubmissionOut,
    GenerateIn,
    JobOut,
    LoginIn,
    MediaIn,
    MediaOut,
    OnboardingIn,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    RegisterIn,
    SiteFileOut,
    TokenOut,
    UserOut,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password
from app.utils import slugify

Base.metadata.create_all(bind=engine)


def _ensure_schema_migrations() -> None:
    """Ajouter colonnes manquantes (migration SQLite légère)."""
    try:
        with engine.connect() as conn:
            cols = conn.execute(_sa_text("PRAGMA table_info(projects)")).fetchall()
            existing = {row[1] for row in cols}
            if "preview_nonce" not in existing:
                conn.execute(_sa_text("ALTER TABLE projects ADD COLUMN preview_nonce VARCHAR"))
                # Backfill pour les projets existants
                from app.models import _nonce  # type: ignore
                rows = conn.execute(_sa_text("SELECT id FROM projects WHERE preview_nonce IS NULL")).fetchall()
                for (pid,) in rows:
                    conn.execute(_sa_text("UPDATE projects SET preview_nonce = :n WHERE id = :id"), {"n": _nonce(), "id": pid})
                conn.commit()
    except Exception as exc:
        # PostgreSQL/Supabase : on ignore, Alembic gérera en prod
        print(f"[migration] skip preview_nonce: {exc}")


_ensure_schema_migrations()

app = FastAPI(
    title="SedApps Simple Backend",
    version="0.1.0",
    description="Backend mono-service simple pour Flutter SedApps",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sedapps-backend"}


# ===== Helpers =====
def get_project_or_404(project_id: str, user: User, db: Session) -> Project:
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project


def ensure_default_site(project: Project) -> None:
    if not project.design_tokens:
        project.design_tokens = {"primary": "#0EA5E9", "secondary": "#38BDF8", "font_heading": "Inter"}
    if not project.sections:
        project.sections = [
            {"id": "hero", "title": "Accueil", "content": f"{project.name}, votre présence web professionnelle.", "enabled": True},
            {"id": "services", "title": "Services", "content": "Des solutions modernes pour votre activité.", "enabled": True},
            {"id": "contact", "title": "Contact", "content": "Contactez-nous pour démarrer votre projet.", "enabled": True},
        ]


# ===== Auth =====
@app.post("/v1/auth/register", response_model=TokenOut, tags=["auth"])
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        org_name=body.org_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenOut(access_token=token, refresh_token=token)


@app.post("/v1/auth/login", response_model=TokenOut, tags=["auth"])
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    token = create_access_token(user.id)
    return TokenOut(access_token=token, refresh_token=token)


@app.get("/v1/account", response_model=UserOut, tags=["account"])
def account(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


# ===== Projects =====
@app.get("/v1/projects", response_model=list[ProjectOut], tags=["projects"])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectOut]:
    return db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()


@app.post("/v1/projects", response_model=ProjectOut, status_code=201, tags=["projects"])
def create_project(body: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectOut:
    project = Project(
        user_id=user.id,
        name=body.name,
        sector=body.sector,
        status="draft",
        domain=f"{slugify(body.name)}.sedapps.cloud",
    )
    ensure_default_site(project)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/v1/projects/{project_id}", response_model=ProjectOut, tags=["projects"])
def get_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectOut:
    return get_project_or_404(project_id, user, db)


@app.patch("/v1/projects/{project_id}", response_model=ProjectOut, tags=["projects"])
def update_project(project_id: str, body: ProjectUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectOut:
    project = get_project_or_404(project_id, user, db)
    if body.name is not None:
        project.name = body.name
    if body.sector is not None:
        project.sector = body.sector
    if body.design_tokens is not None:
        project.design_tokens = body.design_tokens
    if body.sections is not None:
        project.sections = body.sections
    db.commit()
    db.refresh(project)
    return project


# In-memory undo stacks per project (last 30 snapshots of index.html).
_UNDO_STACKS: dict[str, list[str]] = {}
_UNDO_LIMIT = 30


def _push_undo(project_id: str, html_str: str) -> None:
    stack = _UNDO_STACKS.setdefault(project_id, [])
    stack.append(html_str)
    if len(stack) > _UNDO_LIMIT:
        del stack[: len(stack) - _UNDO_LIMIT]


@app.post("/v1/projects/{project_id}/patch_element", tags=["projects"])
def patch_element(
    project_id: str,
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.site_editor import apply_ops
    project = get_project_or_404(project_id, user, db)
    element_id = body.get("element_id")
    ops = body.get("ops") or []
    if not element_id or not isinstance(ops, list):
        raise HTTPException(status_code=400, detail="element_id and ops required")
    files = list(project.generated_files or [])
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == "index.html"), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail="index.html not found")
    current_html = files[idx].get("content", "")
    try:
        new_html, summary = apply_ops(current_html, element_id, ops)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    _push_undo(project_id, current_html)
    files[idx] = {**files[idx], "content": new_html}
    project.generated_files = files
    db.add(project)
    db.commit()
    return {"status": "ok", "element": summary, "can_undo": True, "undo_depth": len(_UNDO_STACKS.get(project_id, []))}


@app.post("/v1/projects/{project_id}/undo", tags=["projects"])
def undo_last_edit(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = get_project_or_404(project_id, user, db)
    stack = _UNDO_STACKS.get(project_id) or []
    if not stack:
        raise HTTPException(status_code=400, detail="rien à annuler")
    previous = stack.pop()
    files = list(project.generated_files or [])
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == "index.html"), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail="index.html not found")
    files[idx] = {**files[idx], "content": previous}
    project.generated_files = files
    db.add(project)
    db.commit()
    return {"status": "ok", "undo_depth": len(stack)}


@app.post("/v1/projects/{project_id}/edit_chat", tags=["projects"])
def edit_chat(
    project_id: str,
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Scoped chat: takes a selected element + user instruction, returns ops to apply."""
    import json
    import httpx
    from app.site_editor import apply_ops

    project = get_project_or_404(project_id, user, db)
    element_id = body.get("element_id")
    instruction = (body.get("instruction") or "").strip()
    selected = body.get("selected") or {}
    if not element_id or not instruction:
        raise HTTPException(status_code=400, detail="element_id and instruction required")

    if not settings.deepseek_api_key:
        raise HTTPException(status_code=400, detail="DEEPSEEK_API_KEY non configurée")

    system_prompt = (
        "Tu es un éditeur visuel de site web. L'utilisateur a sélectionné un élément HTML "
        "et te demande une modification ciblée. Réponds UNIQUEMENT par un JSON: "
        "{\"ops\":[{\"op\":\"set_text\",\"value\":\"...\"},"
        "{\"op\":\"set_attr\",\"name\":\"src\",\"value\":\"...\"},"
        "{\"op\":\"set_style\",\"name\":\"background-color\",\"value\":\"#0ea5e9\"}]}. "
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
                "model": "deepseek-v4-flash",  # rapide pour édition ciblée
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
        raise HTTPException(status_code=502, detail=f"DeepSeek error: {exc}") from exc

    files = list(project.generated_files or [])
    idx = next((i for i, f in enumerate(files) if isinstance(f, dict) and f.get("path") == "index.html"), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail="index.html not found")
    current_html = files[idx].get("content", "")
    try:
        new_html, summary = apply_ops(current_html, element_id, ops)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    _push_undo(project_id, current_html)
    files[idx] = {**files[idx], "content": new_html}
    project.generated_files = files
    db.add(project)
    db.commit()
    return {"status": "ok", "ops": ops, "element": summary, "undo_depth": len(_UNDO_STACKS.get(project_id, []))}


@app.delete("/v1/projects/{project_id}", status_code=204, tags=["projects"])
def delete_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    project = get_project_or_404(project_id, user, db)
    db.delete(project)
    db.commit()


@app.post("/v1/projects/{project_id}/onboarding", response_model=ProjectOut, tags=["projects"])
def save_onboarding(project_id: str, body: OnboardingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectOut:
    project = get_project_or_404(project_id, user, db)
    project.brief = body.model_dump()
    project.sector = body.sector or project.sector
    db.commit()
    db.refresh(project)
    return project


def _run_generation_job(job_id: str, project_id: str, brief: dict) -> None:
    from app.database import SessionLocal
    from sqlalchemy.orm.attributes import flag_modified

    session = SessionLocal()

    def _push_event(event: dict) -> None:
        """Append event to AiJob.input['events'] for SSE streaming."""
        try:
            j = session.get(AiJob, job_id)
            if not j:
                return
            data = dict(j.input or {})
            events = list(data.get("events") or [])
            events.append(event)
            data["events"] = events
            j.input = data
            flag_modified(j, "input")
            session.commit()
        except Exception:
            session.rollback()

    try:
        job = session.get(AiJob, job_id)
        project = session.get(Project, project_id)
        if not job or not project:
            return
        try:
            agents, output, sections, files = generate_llm_site_payload(brief, on_progress=_push_event)
            job.status = "success"
            job.agents = agents
            job.output = output
            job.tokens_in = sum(agent.get("tokens_in", 0) for agent in agents)
            job.tokens_out = sum(agent.get("tokens_out", 0) for agent in agents)
            job.cost_cents = 0
            project.status = "ready"
            project.design_tokens = output["design_tokens"]
            project.sections = sections
            project.generated_files = files
            if not project.preview_nonce:
                project.preview_nonce = secrets.token_urlsafe(12)
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            project.status = "draft"
            _push_event({"step": "error", "status": "failed", "progress": 100, "label": str(exc)})
        job.finished_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


@app.post("/v1/projects/{project_id}/generate", response_model=JobOut, status_code=202, tags=["projects"])
def generate_site(project_id: str, body: GenerateIn, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobOut:
    project = get_project_or_404(project_id, user, db)
    if not project.brief:
        project.brief = {"business_name": project.name, "sector": project.sector or "", "brief": ""}

    project.status = "generating"
    job = AiJob(
        project_id=project.id,
        workflow="site_generation",
        status="running",
        input={"brief": project.brief, "locale": body.locale},
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_generation_job, job.id, project.id, dict(project.brief))
    return job


@app.get("/v1/projects/{project_id}/files", response_model=list[SiteFileOut], tags=["projects"])
def get_project_files(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SiteFileOut]:
    project = get_project_or_404(project_id, user, db)
    return project.generated_files or []


# ===== Public preview (no auth, by nonce) =====

def _find_project_by_nonce(nonce: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.preview_nonce == nonce).first()
    if not project:
        raise HTTPException(status_code=404, detail="preview not found")
    return project


def _find_file(files: list, filename: str) -> dict | None:
    for f in files or []:
        if isinstance(f, dict) and (f.get("path") == filename or f.get("path", "").endswith(f"/{filename}")):
            return f
    return None


@app.get("/v1/p/{nonce}/", include_in_schema=False)
@app.get("/v1/p/{nonce}/index.html", tags=["preview"])
def preview_index(nonce: str, edit: int = 0, db: Session = Depends(get_db)) -> HTMLResponse:
    from app.site_editor import prepare_editable_html
    project = _find_project_by_nonce(nonce, db)
    files = project.generated_files or []
    f = _find_file(files, "index.html")
    if not f:
        return HTMLResponse(
            "<!doctype html><html><body style='font-family:sans-serif;padding:40px;text-align:center;color:#64748b'>"
            "<h2>Aperçu en cours de génération…</h2>"
            "<p>Le site n'a pas encore été généré.</p></body></html>",
            status_code=200,
        )
    content = f.get("content", "")
    if edit:
        content = prepare_editable_html(content)
    return HTMLResponse(content=content, status_code=200)


@app.get("/v1/p/{nonce}/{filename}", tags=["preview"])
def preview_asset(
    nonce: str,
    filename: str = Path(..., pattern=r"^[a-zA-Z0-9_\-./]+$"),
    db: Session = Depends(get_db),
) -> Response:
    project = _find_project_by_nonce(nonce, db)
    files = project.generated_files or []
    f = _find_file(files, filename)
    if not f:
        raise HTTPException(status_code=404, detail="asset not found")
    mime, _ = mimetypes.guess_type(filename)
    if mime is None:
        if filename.endswith(".css"):
            mime = "text/css"
        elif filename.endswith(".js"):
            mime = "application/javascript"
        else:
            mime = "text/plain"
    content = f.get("content", "")
    return Response(content=content, media_type=mime)


# ===== SSE job stream =====

@app.get("/v1/jobs/{job_id}/stream", tags=["jobs"])
async def stream_job(
    job_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # Authentification via query param (compatible EventSource)
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")

    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    project = db.get(Project, job.project_id)
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")

    async def event_generator():
        from app.database import SessionLocal
        last_count = 0
        max_iterations = 300  # 5 minutes max (300 * 1s)
        for _ in range(max_iterations):
            local = SessionLocal()
            try:
                j = local.get(AiJob, job_id)
                if not j:
                    yield f"event: error\ndata: {_json.dumps({'message': 'job disappeared'})}\n\n"
                    return
                events = (j.input or {}).get("events") or []
                # Push new events
                while last_count < len(events):
                    evt = events[last_count]
                    yield f"data: {_json.dumps(evt, ensure_ascii=False)}\n\n"
                    last_count += 1
                if j.status in ("success", "failed"):
                    final = {"step": "complete", "status": j.status, "progress": 100, "project_id": j.project_id}
                    yield f"event: complete\ndata: {_json.dumps(final)}\n\n"
                    return
            finally:
                local.close()
            await asyncio.sleep(1.0)
        yield f"event: timeout\ndata: {{}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/v1/projects/{project_id}/plan", tags=["projects"])
def get_project_plan(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(project_id, user, db)
    brief = project.brief or {}
    if not brief:
        return {"error": "No brief available"}
    plan = generate_project_plan(brief)
    return plan


@app.post("/v1/projects/{project_id}/chat", tags=["projects"])
def chat_with_project(
    project_id: str,
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    import json
    import httpx

    project = get_project_or_404(project_id, user, db)
    messages_in = body.get("messages") or []
    if not isinstance(messages_in, list) or not messages_in:
        raise HTTPException(status_code=400, detail="messages required")

    brief = project.brief or {}
    tokens = project.design_tokens or {}
    sections = project.sections or []
    section_summary = ", ".join(
        f"{s.get('id', '?')}: {str(s.get('content', ''))[:60]}" for s in sections if isinstance(s, dict)
    )
    system_prompt = (
        "Tu es un assistant IA expert en création de sites web pour la plateforme SedApps. "
        "Tu aides l'utilisateur à itérer sur son site déjà généré. Reste concret, concis, en français. "
        f"Contexte projet : nom={project.name}, secteur={project.sector or ''}. "
        f"Brief onboarding : {json.dumps(brief, ensure_ascii=False)}. "
        f"Design tokens : {json.dumps(tokens, ensure_ascii=False)}. "
        f"Sections actuelles : {section_summary or 'aucune'}. "
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
            raise HTTPException(status_code=502, detail=f"DeepSeek HTTP {response.status_code}: {detail}")
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek error: {type(exc).__name__}: {exc}") from exc

    return {"message": content}


def get_user_from_download_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid download token") from exc
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid download token")
    return user


@app.get("/v1/projects/{project_id}/download", tags=["projects"])
def download_project_zip(project_id: str, token: str = Query(...), db: Session = Depends(get_db)) -> StreamingResponse:
    user = get_user_from_download_token(token, db)
    project = get_project_or_404(project_id, user, db)
    files = project.generated_files or []
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no generated files available")
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for item in files:
            path = str(item.get("path") or "").strip().lstrip("/")
            content = str(item.get("content") or "")
            if path and ".." not in path.split("/"):
                zip_file.writestr(path, content)
    archive.seek(0)
    filename = f"{slugify(project.name)}-{project.id}.zip"
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/v1/projects/{project_id}/deploy", response_model=DeploymentOut, status_code=202, tags=["projects"])
def deploy_project(project_id: str, body: DeployIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DeploymentOut:
    project = get_project_or_404(project_id, user, db)
    domain = body.custom_domain or project.domain or f"{slugify(project.name)}.sedapps.cloud"
    project.status = "published"
    project.domain = domain
    project.published_url = f"https://{domain}"
    db.commit()
    return DeploymentOut(id=str(uuid.uuid4()), project_id=project.id, status="published", domain=domain, url=project.published_url)


# ===== Jobs =====
@app.get("/v1/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobOut:
    job = db.get(AiJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    project = get_project_or_404(job.project_id, user, db)
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job


# ===== Articles CMS =====
@app.get("/v1/projects/{project_id}/articles", response_model=list[ArticleOut], tags=["cms"])
def list_articles(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ArticleOut]:
    project = get_project_or_404(project_id, user, db)
    return db.query(Article).filter(Article.project_id == project.id).order_by(Article.created_at.desc()).all()


@app.post("/v1/projects/{project_id}/articles", response_model=ArticleOut, status_code=201, tags=["cms"])
def create_article(project_id: str, body: ArticleCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ArticleOut:
    project = get_project_or_404(project_id, user, db)
    article = Article(project_id=project.id, title=body.title, slug=slugify(body.title), markdown=body.markdown, status=body.status)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@app.patch("/v1/projects/{project_id}/articles/{article_id}", response_model=ArticleOut, tags=["cms"])
def update_article(project_id: str, article_id: str, body: ArticleUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ArticleOut:
    project = get_project_or_404(project_id, user, db)
    article = db.get(Article, article_id)
    if not article or article.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    if body.title is not None:
        article.title = body.title
        article.slug = slugify(body.title)
    if body.markdown is not None:
        article.markdown = body.markdown
    if body.status is not None:
        article.status = body.status
    db.commit()
    db.refresh(article)
    return article


@app.delete("/v1/projects/{project_id}/articles/{article_id}", status_code=204, tags=["cms"])
def delete_article(project_id: str, article_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    project = get_project_or_404(project_id, user, db)
    article = db.get(Article, article_id)
    if not article or article.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    db.delete(article)
    db.commit()


# ===== Forms / Comments / Media =====
@app.post("/v1/projects/{project_id}/forms/submissions", response_model=FormSubmissionOut, status_code=201, tags=["forms"])
def create_form_submission(project_id: str, body: FormSubmissionIn, db: Session = Depends(get_db)) -> FormSubmissionOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    row = FormSubmission(project_id=project.id, form_name=body.form_name, data=body.data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/v1/projects/{project_id}/forms/submissions", response_model=list[FormSubmissionOut], tags=["forms"])
def list_form_submissions(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[FormSubmissionOut]:
    project = get_project_or_404(project_id, user, db)
    return db.query(FormSubmission).filter(FormSubmission.project_id == project.id).order_by(FormSubmission.created_at.desc()).all()


@app.post("/v1/comments", response_model=CommentOut, status_code=201, tags=["comments"])
def create_comment(body: CommentIn, db: Session = Depends(get_db)) -> CommentOut:
    article = db.get(Article, body.article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    comment = Comment(article_id=article.id, author=body.author, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/v1/projects/{project_id}/comments", response_model=list[CommentOut], tags=["comments"])
def list_comments(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CommentOut]:
    project = get_project_or_404(project_id, user, db)
    rows = db.query(Comment).join(Article, Comment.article_id == Article.id).filter(Article.project_id == project.id).order_by(Comment.created_at.desc()).all()
    return rows


@app.patch("/v1/comments/{comment_id}", response_model=CommentOut, tags=["comments"])
def moderate_comment(comment_id: str, body: CommentUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CommentOut:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="comment not found")
    article = db.get(Article, comment.article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    get_project_or_404(article.project_id, user, db)
    comment.status = body.status
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/v1/projects/{project_id}/media", response_model=list[MediaOut], tags=["media"])
def list_media(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MediaOut]:
    project = get_project_or_404(project_id, user, db)
    return db.query(MediaAsset).filter(MediaAsset.project_id == project.id).order_by(MediaAsset.created_at.desc()).all()


@app.post("/v1/projects/{project_id}/media", response_model=MediaOut, status_code=201, tags=["media"])
def create_media(project_id: str, body: MediaIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MediaOut:
    project = get_project_or_404(project_id, user, db)
    media = MediaAsset(project_id=project.id, filename=body.filename, url=body.url, mime_type=body.mime_type, size_bytes=body.size_bytes)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media
