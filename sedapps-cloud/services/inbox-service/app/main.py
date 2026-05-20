from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Form as FormField, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Form, FormSubmission, SubmissionStatus
from app.services import SubmissionValidationError, normalize_submission

app = FastAPI(title="SedApps Inbox Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "inbox-service"}


@app.post("/v1/forms/{form_id}/submit")
async def submit_form(
    form_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "form not found")

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        raw = await request.json()
    else:
        raw_form = await request.form()
        raw = dict(raw_form)

    try:
        data, is_spam = normalize_submission(raw, form.schema)
    except SubmissionValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    submission = FormSubmission(
        tenant_id=form.tenant_id,
        project_id=form.project_id,
        form_id=form.id,
        data=data,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
        status=SubmissionStatus.spam if is_spam else SubmissionStatus.new,
    )
    db.add(submission)
    db.commit()

    success = form.schema.get("success_message") or "Merci, votre message a bien été envoyé."
    return {"status": "ok", "message": success, "submission_id": str(submission.id)}


@app.post("/v1/forms/{form_id}/submit-redirect")
async def submit_form_redirect(
    form_id: uuid.UUID,
    request: Request,
    redirect_to: Annotated[str | None, FormField()] = None,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return await submit_form(form_id=form_id, request=request, db=db)
