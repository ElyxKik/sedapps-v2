from __future__ import annotations

import re
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.domain import Domain, DomainStatus
from app.models.project import Project
from app.schemas.domain import DomainAssign, DomainCreate, DomainOut, DomainSearchOut, SubdomainCreate
from app.services.ovh_client import OvhClient

router = APIRouter()
DOMAIN_RE = re.compile(r"^(?=.{3,255}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def _normalize(value: str) -> str:
    domain = value.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")
    if not DOMAIN_RE.fullmatch(domain):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "invalid domain name")
    return domain


def _owned(db: Session, domain_id: uuid.UUID) -> Domain:
    row = db.get(Domain, domain_id)
    if not row or row.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "domain not found")
    return row


@router.get("", response_model=list[DomainOut])
def list_domains(db: Session = Depends(get_current_org_db)) -> list[Domain]:
    return db.query(Domain).filter(Domain.tenant_id == db.info["tenant_id"]).order_by(Domain.name).all()


@router.get("/search", response_model=DomainSearchOut)
def search_domain(q: str = Query(min_length=3, max_length=255), db: Session = Depends(get_current_org_db)) -> DomainSearchOut:
    name = _normalize(q)
    already_managed = db.query(Domain.id).filter(Domain.name == name).first() is not None
    if already_managed:
        return DomainSearchOut(domain=name, available=False, checked=True, source="salaai", message="Déjà ajouté dans Sala AI.")
    result = OvhClient().availability(name)
    return DomainSearchOut(domain=name, available=result.available, checked=result.checked, source=result.source, message=result.message)


@router.post("", response_model=DomainOut, status_code=201)
def add_domain(body: DomainCreate, db: Session = Depends(get_current_org_db)) -> Domain:
    name = _normalize(body.name)
    if db.query(Domain.id).filter(Domain.name == name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "domain already managed")
    lookup = OvhClient().availability(name)
    if not lookup.checked:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, lookup.message)
    if lookup.available:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "domain is available but has not been purchased; buy it from a registrar before connecting it",
        )
    row = Domain(
        tenant_id=db.info["tenant_id"],
        name=name,
        provider=body.provider,
        expires_at=body.expires_at,
        status=DomainStatus.pending,
        verification_token=secrets.token_urlsafe(24),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{domain_id}/verify", response_model=DomainOut)
def verify_domain(domain_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> Domain:
    row = _owned(db, domain_id)
    if row.parent_domain_id is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "subdomains inherit verification")
    if row.status == DomainStatus.active:
        return row
    if not row.verification_name or not row.verification_value:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "verification is unavailable")
    if not OvhClient.has_verification_record(row.verification_name, row.verification_value):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "TXT verification record was not found yet",
        )
    row.status = DomainStatus.active
    db.commit()
    db.refresh(row)
    return row


@router.post("/{domain_id}/subdomains", response_model=DomainOut, status_code=201)
def add_subdomain(domain_id: uuid.UUID, body: SubdomainCreate, db: Session = Depends(get_current_org_db)) -> Domain:
    parent = _owned(db, domain_id)
    if parent.parent_domain_id is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "select a root domain")
    if parent.status != DomainStatus.active:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "verify the root domain first")
    name = f"{body.label.lower()}.{parent.name}"
    if db.query(Domain.id).filter(Domain.name == name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "subdomain already exists")
    row = Domain(tenant_id=db.info["tenant_id"], name=name, provider=parent.provider, status=DomainStatus.active, parent_domain_id=parent.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{domain_id}/assignment", response_model=DomainOut)
def assign_domain(domain_id: uuid.UUID, body: DomainAssign, db: Session = Depends(get_current_org_db)) -> Domain:
    row = _owned(db, domain_id)
    if body.project_id is not None and row.status != DomainStatus.active:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "verify the domain before assigning it")
    if body.project_id is not None:
        project = db.get(Project, body.project_id)
        if not project or project.tenant_id != db.info["tenant_id"]:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
        db.query(Domain).filter(
            Domain.project_id == body.project_id, Domain.id != row.id
        ).update({Domain.project_id: None}, synchronize_session=False)
        project.custom_domain = row.name
    elif row.project_id is not None:
        project = db.get(Project, row.project_id)
        if project and project.custom_domain == row.name:
            project.custom_domain = None
    row.project_id = body.project_id
    db.commit()
    db.refresh(row)
    return row


@router.post("/{domain_id}/renew")
def renew_domain(domain_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> dict[str, object]:
    row = _owned(db, domain_id)
    if row.parent_domain_id is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "subdomains do not require renewal")
    return {"domain_id": str(row.id), "renewal_requested": True}
