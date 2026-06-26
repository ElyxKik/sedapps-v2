from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_db_no_tenant
from app.models.membership import Membership
from app.models.user import User
from app.schemas.auth import MeOut

router = APIRouter()


@router.get("", response_model=MeOut)
def get_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_no_tenant),
) -> MeOut:
    mem = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not mem:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no organization")
    return MeOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        locale=user.locale,
        org_id=str(mem.org_id),
        role=mem.role.value,
    )
