from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_db_no_tenant
from app.config import settings
from app.models.credit_transaction import CreditTransaction
from app.models.domain import Domain
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.services.credits import grant_bonus_credits, organization_wallet_snapshot

router = APIRouter()


def require_admin(
    secret: str = Header(default="", alias="X-Admin-Secret"),
) -> None:
    expected = settings.SEDAPPS_ADMIN_SECRET or settings.INTERNAL_API_TOKEN
    if not expected or secret != expected:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")


class CreditGrantIn(BaseModel):
    userId: uuid.UUID
    credits: int = Field(gt=0, le=1_000_000)
    description: str | None = Field(default=None, max_length=500)
    type: str = "manual"


class UserActionIn(BaseModel):
    action: str
    userId: uuid.UUID


def _membership(db: Session, user_id: uuid.UUID) -> Membership:
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user_id)
        .order_by(Membership.created_at.asc())
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user organization not found")
    return membership


def _totals(db: Session, user_id: uuid.UUID) -> tuple[int, int, int]:
    granted = (
        db.query(func.coalesce(func.sum(CreditTransaction.credits_delta), 0))
        .filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.credits_delta > 0,
        )
        .scalar()
    )
    consumed = (
        db.query(func.coalesce(func.sum(-CreditTransaction.credits_delta), 0))
        .filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.credits_delta < 0,
        )
        .scalar()
    )
    tokens = (
        db.query(
            func.coalesce(
                func.sum(CreditTransaction.tokens_in + CreditTransaction.tokens_out),
                0,
            )
        )
        .filter(CreditTransaction.user_id == user_id)
        .scalar()
    )
    return int(granted or 0), int(consumed or 0), int(tokens or 0)


def _user_row(
    db: Session, user: User, organization: Organization | None
) -> dict:
    granted, consumed, tokens = _totals(db, user.id)
    wallet = organization_wallet_snapshot(organization) if organization else {}
    active_at = user.created_at.isoformat() if user.is_active else None
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.full_name or user.email.split("@")[0],
        "createdAt": user.created_at.isoformat(),
        "created_at": user.created_at.isoformat(),
        "email_confirmed_at": active_at,
        "banned_until": None if user.is_active else "9999-12-31T23:59:59+00:00",
        "last_sign_in_at": None,
        "user_metadata": {"full_name": user.full_name},
        "organization_id": str(organization.id) if organization else None,
        "organization_name": organization.name if organization else None,
        "plan": organization.plan if organization else "free",
        "balance": int(wallet.get("available_credits", 0)),
        "includedQuota": int(wallet.get("monthly_quota_credits", 0)),
        "bonusBalance": int(wallet.get("bonus_credits", 0)),
        "reserved": int(wallet.get("reserved_credits", 0)),
        "usedThisMonth": int(wallet.get("used_this_month_credits", 0)),
        "totalPurchased": granted,
        "totalConsumed": consumed,
        "totalTokens": tokens,
    }


@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(
    search: str = Query(default="", max_length=255),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db_no_tenant),
) -> dict:
    query = db.query(User)
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
        )
    rows = query.order_by(User.created_at.desc()).limit(limit).all()
    users = []
    for user in rows:
        membership = (
            db.query(Membership)
            .filter(Membership.user_id == user.id)
            .order_by(Membership.created_at.asc())
            .first()
        )
        organization = db.get(Organization, membership.org_id) if membership else None
        users.append(_user_row(db, user, organization))
    db.commit()
    return {"users": users}


@router.get("/users/{user_id}", dependencies=[Depends(require_admin)])
def user_detail(
    user_id: uuid.UUID, db: Session = Depends(get_db_no_tenant)
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    membership = _membership(db, user.id)
    organization = db.get(Organization, membership.org_id)
    projects = (
        db.query(Project)
        .filter(Project.tenant_id == membership.org_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    domains = (
        db.query(Domain)
        .filter(Domain.tenant_id == membership.org_id)
        .order_by(Domain.created_at.desc())
        .all()
    )
    user_payload = _user_row(db, user, organization)
    db.commit()
    return {
        "user": user_payload,
        "projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "domain": project.custom_domain,
                "stack_type": "generated",
                "status": project.status.value,
                "visits": 0,
                "created_at": project.created_at.isoformat(),
            }
            for project in projects
        ],
        "subscriptions": [],
        "domains": [
            {
                "id": str(domain.id),
                "domain": domain.name,
                "verified": domain.status.value == "active",
                "created_at": domain.created_at.isoformat(),
            }
            for domain in domains
        ],
    }


@router.get(
    "/users/{user_id}/credits", dependencies=[Depends(require_admin)]
)
def user_credits(
    user_id: uuid.UUID, db: Session = Depends(get_db_no_tenant)
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    membership = _membership(db, user.id)
    organization = db.get(Organization, membership.org_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    wallet = organization_wallet_snapshot(organization)
    granted, consumed, tokens = _totals(db, user.id)
    transactions = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(100)
        .all()
    )
    db.commit()
    return {
        "balance": {
            "balance": wallet["available_credits"],
            "included_quota": wallet["monthly_quota_credits"],
            "bonus_balance": wallet["bonus_credits"],
            "reserved": wallet["reserved_credits"],
            "used_this_month": wallet["used_this_month_credits"],
            "total_purchased": granted,
            "total_consumed": consumed,
            "total_tokens": tokens,
        },
        "transactions": [
            {
                "id": str(transaction.id),
                "type": transaction.type,
                "credits_delta": transaction.credits_delta,
                "balance_after": transaction.balance_after,
                "generation_type": transaction.operation,
                "tokens_used": transaction.tokens_in + transaction.tokens_out,
                "tokens_in": transaction.tokens_in,
                "tokens_out": transaction.tokens_out,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
            }
            for transaction in transactions
        ],
    }


@router.post("/credits/add", dependencies=[Depends(require_admin)])
def add_credits(
    body: CreditGrantIn, db: Session = Depends(get_db_no_tenant)
) -> dict:
    user = db.get(User, body.userId)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    membership = _membership(db, user.id)
    try:
        transaction = grant_bonus_credits(
            db,
            tenant_id=membership.org_id,
            user_id=user.id,
            credits=body.credits,
            transaction_type=body.type,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    db.flush()
    organization = db.get(Organization, membership.org_id)
    wallet = organization_wallet_snapshot(organization)
    db.commit()
    return {
        "ok": True,
        "message": f"{body.credits} crédits ajoutés à {user.email}",
        "transaction_id": str(transaction.id),
        "balance": wallet["available_credits"],
        "bonus_balance": wallet["bonus_credits"],
    }


@router.post("/users/actions", dependencies=[Depends(require_admin)])
def user_action(
    body: UserActionIn, db: Session = Depends(get_db_no_tenant)
) -> dict:
    user = db.get(User, body.userId)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    if body.action == "ban":
        user.is_active = False
    elif body.action == "unban":
        user.is_active = True
    elif body.action == "delete":
        memberships = (
            db.query(Membership).filter(Membership.user_id == user.id).all()
        )
        for membership in memberships:
            member_count = (
                db.query(func.count(Membership.user_id))
                .filter(Membership.org_id == membership.org_id)
                .scalar()
            )
            if member_count == 1:
                organization = db.get(Organization, membership.org_id)
                if organization:
                    db.delete(organization)
        db.delete(user)
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "unknown action")
    db.commit()
    return {"ok": True, "action": body.action}
