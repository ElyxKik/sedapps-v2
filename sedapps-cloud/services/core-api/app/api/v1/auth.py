from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_db_no_tenant
from app.auth.jwt import create_token, decode_token
from app.auth.password import hash_password, verify_password
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import LoginIn, MeOut, RefreshIn, RegisterIn, TokenPair

router = APIRouter()


def _issue_pair(user: User, org_id: uuid.UUID) -> TokenPair:
    extra = {"org": str(org_id)}
    return TokenPair(
        access_token=create_token(str(user.id), "access", extra=extra),
        refresh_token=create_token(str(user.id), "refresh", extra=extra),
    )


@router.post("/register", response_model=TokenPair, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db_no_tenant)) -> TokenPair:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "email already used")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    org = Organization(name=body.org_name, plan="free")
    db.add_all([user, org])
    db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role=Role.owner))
    db.commit()
    return _issue_pair(user, org.id)


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: Session = Depends(get_db_no_tenant)) -> TokenPair:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    mem = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not mem:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no organization")
    return _issue_pair(user, mem.org_id)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, db: Session = Depends(get_db_no_tenant)) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid: {e}") from e
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong token type")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return _issue_pair(user, uuid.UUID(payload["org"]))


@router.get("/me", response_model=MeOut)
def me(
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
