from __future__ import annotations

from slugify import slugify
from sqlalchemy.orm import Session


def unique_slug(db: Session, model, project_id, base: str, field: str = "slug") -> str:
    base = slugify(base) or "item"
    candidate = base
    n = 1
    while (
        db.query(model)
        .filter(getattr(model, field) == candidate, model.project_id == project_id)
        .first()
    ):
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def unique_global_slug(db: Session, model, base: str, field: str = "slug") -> str:
    base = slugify(base) or "item"
    candidate = base
    n = 1
    while db.query(model).filter(getattr(model, field) == candidate).first():
        n += 1
        candidate = f"{base}-{n}"
    return candidate
