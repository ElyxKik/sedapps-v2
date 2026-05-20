from __future__ import annotations

import uuid
from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.db.session import SessionLocal, set_tenant
from app.models.membership import Membership
from app.models.user import User

bearer = HTTPBearer(auto_error=True)


def get_db_no_tenant() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db_no_tenant),
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}") from e

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")

    user_id = payload.get("sub")
    user = db.get(User, uuid.UUID(user_id)) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


def get_current_org_db(
    user: User = Depends(get_current_user),
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db_no_tenant),
) -> Session:
    """
    Returns a Session bound to the user's active organization.
    The active org is taken from the JWT 'org' claim, or the user's first membership.
    Sets Postgres `app.current_tenant` so RLS policies apply.
    """
    payload = decode_token(creds.credentials)
    org_id_claim = payload.get("org")
    if org_id_claim:
        org_id = uuid.UUID(org_id_claim)
        mem = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.org_id == org_id)
            .first()
        )
    else:
        mem = db.query(Membership).filter(Membership.user_id == user.id).first()

    if not mem:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no organization membership")

    set_tenant(db, str(mem.org_id))
    # Stash on session for downstream usage if needed
    db.info["tenant_id"] = mem.org_id
    db.info["user_id"] = user.id
    db.info["role"] = mem.role
    return db


def require_role(*roles: str):
    def _dep(db: Session = Depends(get_current_org_db)) -> Session:
        if db.info.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return db

    return _dep
