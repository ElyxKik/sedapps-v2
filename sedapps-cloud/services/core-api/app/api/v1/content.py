from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.form import Form, FormSubmission, SubmissionStatus
from app.models.article import Article
from app.models.comment import Comment, CommentStatus
from app.models.media import Media
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if not project or project.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return project


class FormIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    form_schema: dict = Field(default_factory=dict, alias="schema")

    model_config = {"populate_by_name": True}


class SubmissionUpdate(BaseModel):
    status: SubmissionStatus


class MediaIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime: str = Field(min_length=1, max_length=80)
    size_bytes: int = Field(ge=0)
    s3_key: str = Field(min_length=1, max_length=500)
    width: int | None = Field(None, ge=1)
    height: int | None = Field(None, ge=1)
    alt: str | None = Field(None, max_length=255)
    folder: str | None = Field(None, max_length=120)


class CommentIn(BaseModel):
    article_id: uuid.UUID
    author_name: str = Field(min_length=1, max_length=120)
    author_email: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=1, max_length=10000)


class CommentUpdate(BaseModel):
    status: CommentStatus


def _form_out(form: Form, count: int = 0) -> dict:
    return {
        "id": str(form.id),
        "name": form.name,
        "schema": form.schema,
        "submission_count": count,
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat(),
    }


@router.get("/{project_id}/forms")
def list_forms(project_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> list[dict]:
    _project(db, project_id)
    counts = dict(
        db.query(FormSubmission.form_id, func.count(FormSubmission.id))
        .filter(FormSubmission.project_id == project_id)
        .group_by(FormSubmission.form_id)
        .all()
    )
    rows = db.query(Form).filter(Form.project_id == project_id).order_by(Form.created_at.desc()).all()
    return [_form_out(row, counts.get(row.id, 0)) for row in rows]


@router.post("/{project_id}/forms", status_code=201)
def create_form(
    project_id: uuid.UUID, body: FormIn, db: Session = Depends(get_current_org_db)
) -> dict:
    project = _project(db, project_id)
    form = Form(
        tenant_id=project.tenant_id,
        project_id=project.id,
        name=body.name,
        schema=body.form_schema,
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return _form_out(form)


@router.delete("/{project_id}/forms/{form_id}", status_code=204, response_class=Response)
def delete_form(
    project_id: uuid.UUID, form_id: uuid.UUID, db: Session = Depends(get_current_org_db)
) -> Response:
    _project(db, project_id)
    form = db.get(Form, form_id)
    if not form or form.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "form not found")
    db.delete(form)
    db.commit()
    return Response(status_code=204)


@router.get("/{project_id}/submissions")
def list_submissions(
    project_id: uuid.UUID, db: Session = Depends(get_current_org_db)
) -> list[dict]:
    _project(db, project_id)
    rows = (
        db.query(FormSubmission, Form.name)
        .join(Form, Form.id == FormSubmission.form_id)
        .filter(FormSubmission.project_id == project_id)
        .order_by(FormSubmission.created_at.desc())
        .limit(500)
        .all()
    )
    return [
        {
            "id": str(row.id),
            "form_id": str(row.form_id),
            "form_name": form_name,
            "data": row.data,
            "status": row.status.value,
            "created_at": row.created_at.isoformat(),
        }
        for row, form_name in rows
    ]


@router.patch("/{project_id}/submissions/{submission_id}")
def update_submission(
    project_id: uuid.UUID,
    submission_id: uuid.UUID,
    body: SubmissionUpdate,
    db: Session = Depends(get_current_org_db),
) -> dict:
    _project(db, project_id)
    submission = db.get(FormSubmission, submission_id)
    if not submission or submission.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "submission not found")
    submission.status = body.status
    db.commit()
    return {"id": str(submission.id), "status": submission.status.value}


def _media_out(media: Media) -> dict:
    return {
        "id": str(media.id),
        "filename": media.filename,
        "mime": media.mime,
        "size_bytes": media.size_bytes,
        "s3_key": media.s3_key,
        "width": media.width,
        "height": media.height,
        "alt": media.alt,
        "folder": media.folder,
        "created_at": media.created_at.isoformat(),
    }


@router.get("/{project_id}/media")
def list_media(project_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> list[dict]:
    _project(db, project_id)
    rows = db.query(Media).filter(Media.project_id == project_id).order_by(Media.created_at.desc()).all()
    return [_media_out(row) for row in rows]


@router.post("/{project_id}/media", status_code=201)
def create_media(
    project_id: uuid.UUID, body: MediaIn, db: Session = Depends(get_current_org_db)
) -> dict:
    project = _project(db, project_id)
    media = Media(tenant_id=project.tenant_id, project_id=project.id, **body.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return _media_out(media)


@router.delete("/{project_id}/media/{media_id}", status_code=204, response_class=Response)
def delete_media(
    project_id: uuid.UUID, media_id: uuid.UUID, db: Session = Depends(get_current_org_db)
) -> Response:
    _project(db, project_id)
    media = db.get(Media, media_id)
    if not media or media.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "media not found")
    db.delete(media)
    db.commit()
    return Response(status_code=204)


def _comment_out(comment: Comment) -> dict:
    return {
        "id": str(comment.id),
        "article_id": str(comment.article_id),
        "author_name": comment.author_name,
        "author_email": comment.author_email,
        "content": comment.content,
        "status": comment.status.value,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("/{project_id}/comments")
def list_comments(
    project_id: uuid.UUID, db: Session = Depends(get_current_org_db)
) -> list[dict]:
    _project(db, project_id)
    rows = (
        db.query(Comment)
        .filter(Comment.project_id == project_id)
        .order_by(Comment.created_at.desc())
        .limit(500)
        .all()
    )
    return [_comment_out(row) for row in rows]


@router.post("/{project_id}/comments", status_code=201)
def create_comment(
    project_id: uuid.UUID, body: CommentIn, db: Session = Depends(get_current_org_db)
) -> dict:
    project = _project(db, project_id)
    article = db.get(Article, body.article_id)
    if not article or article.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")
    comment = Comment(
        tenant_id=project.tenant_id,
        project_id=project.id,
        status=CommentStatus.pending,
        **body.model_dump(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment)


@router.patch("/{project_id}/comments/{comment_id}")
def update_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: CommentUpdate,
    db: Session = Depends(get_current_org_db),
) -> dict:
    _project(db, project_id)
    comment = db.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "comment not found")
    comment.status = body.status
    db.commit()
    return _comment_out(comment)


@router.delete("/{project_id}/comments/{comment_id}", status_code=204, response_class=Response)
def delete_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> Response:
    _project(db, project_id)
    comment = db.get(Comment, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "comment not found")
    db.delete(comment)
    db.commit()
    return Response(status_code=204)
