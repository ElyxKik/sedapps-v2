from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.article import Article, ArticleStatus
from app.models.project import Project
from app.schemas.article import ArticleCreate, ArticleOut, ArticleUpdate
from app.services.slug import unique_slug

router = APIRouter()


def _reading_time(md: str) -> int:
    words = len((md or "").split())
    return max(1, round(words / 200))


def _project_or_404(db: Session, project_id: uuid.UUID) -> Project:
    p = db.get(Project, project_id)
    if not p or p.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return p


@router.get("/{project_id}/articles", response_model=list[ArticleOut])
def list_articles(
    project_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> list[ArticleOut]:
    _project_or_404(db, project_id)
    rows = (
        db.query(Article)
        .filter(Article.project_id == project_id)
        .order_by(Article.created_at.desc())
        .all()
    )
    return [ArticleOut.model_validate(r) for r in rows]


@router.post("/{project_id}/articles", response_model=ArticleOut, status_code=201)
def create_article(
    project_id: uuid.UUID,
    body: ArticleCreate,
    db: Session = Depends(get_current_org_db),
) -> ArticleOut:
    project = _project_or_404(db, project_id)
    slug = unique_slug(db, Article, project.id, body.slug or body.title)
    article = Article(
        tenant_id=project.tenant_id,
        project_id=project.id,
        slug=slug,
        title=body.title,
        excerpt=body.excerpt,
        cover_url=body.cover_url,
        content_md=body.content_md,
        status=body.status,
        scheduled_at=body.scheduled_at,
        seo=body.seo,
        reading_time_min=_reading_time(body.content_md),
        published_at=datetime.now(timezone.utc) if body.status == ArticleStatus.published else None,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return ArticleOut.model_validate(article)


@router.patch("/{project_id}/articles/{article_id}", response_model=ArticleOut)
def update_article(
    project_id: uuid.UUID,
    article_id: uuid.UUID,
    body: ArticleUpdate,
    db: Session = Depends(get_current_org_db),
) -> ArticleOut:
    project = _project_or_404(db, project_id)
    article = db.get(Article, article_id)
    if not article or article.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")

    data = body.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        data["slug"] = unique_slug(db, Article, project.id, data["slug"])
    if "content_md" in data and data["content_md"] is not None:
        article.reading_time_min = _reading_time(data["content_md"])
    if data.get("status") == ArticleStatus.published and not article.published_at:
        article.published_at = datetime.now(timezone.utc)

    for k, v in data.items():
        setattr(article, k, v)

    db.commit()
    db.refresh(article)
    return ArticleOut.model_validate(article)


@router.delete(
    "/{project_id}/articles/{article_id}",
    status_code=204,
    response_class=Response,
)
def delete_article(
    project_id: uuid.UUID,
    article_id: uuid.UUID,
    db: Session = Depends(get_current_org_db),
) -> Response:
    project = _project_or_404(db, project_id)
    article = db.get(Article, article_id)
    if not article or article.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")
    db.delete(article)
    db.commit()
    return Response(status_code=204)
