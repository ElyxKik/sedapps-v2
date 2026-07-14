from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_db_no_tenant
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import AccountOut, AccountUpdate

router = APIRouter()


def _account(user: User, membership: Membership, organization: Organization) -> AccountOut:
    return AccountOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        locale=user.locale,
        org_id=str(membership.org_id),
        role=membership.role.value,
        org_name=organization.name,
        plan=organization.plan,
    )


@router.get("", response_model=AccountOut)
def get_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_no_tenant),
) -> AccountOut:
    mem = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not mem:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no organization")
    organization = db.get(Organization, mem.org_id)
    if not organization:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    return _account(user, mem, organization)


@router.patch("", response_model=AccountOut)
def update_account(
    body: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_no_tenant),
) -> AccountOut:
    mem = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not mem:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no organization")
    organization = db.get(Organization, mem.org_id)
    if not organization:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    data = body.model_dump(exclude_unset=True)
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "locale" in data:
        user.locale = data["locale"]
    if "org_name" in data:
        organization.name = data["org_name"]
    db.commit()
    db.refresh(user)
    db.refresh(organization)
    return _account(user, mem, organization)
