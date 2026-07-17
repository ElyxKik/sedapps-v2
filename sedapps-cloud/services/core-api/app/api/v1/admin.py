from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_db_no_tenant
from app.config import settings
from app.models.credit_transaction import CreditTransaction
from app.models.domain import Domain, DomainStatus
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.models.ai_job import AiJob, JobStatus
from app.services.credits import grant_bonus_credits, organization_wallet_snapshot

router = APIRouter()


def _month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def _previous_month_start(now: datetime) -> datetime:
    if now.month == 1:
        return datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    return datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)


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


def _monthly_usage(db: Session, user_id: uuid.UUID) -> tuple[int, int]:
    month_start = _month_start(datetime.now(timezone.utc))
    row = (
        db.query(
            func.coalesce(func.sum(-CreditTransaction.credits_delta), 0),
            func.coalesce(
                func.sum(CreditTransaction.tokens_in + CreditTransaction.tokens_out),
                0,
            ),
        )
        .filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.credits_delta < 0,
            CreditTransaction.created_at >= month_start,
        )
        .one()
    )
    return int(row[0] or 0), int(row[1] or 0)


def _user_row(
    db: Session, user: User, organization: Organization | None
) -> dict:
    granted, consumed, tokens = _totals(db, user.id)
    monthly_consumed, monthly_tokens = _monthly_usage(db, user.id)
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
        "includedRemaining": max(
            0,
            int(wallet.get("monthly_quota_credits", 0))
            - int(wallet.get("used_this_month_credits", 0)),
        ),
        "bonusBalance": int(wallet.get("bonus_credits", 0)),
        "reserved": int(wallet.get("reserved_credits", 0)),
        "usedThisMonth": monthly_consumed,
        "tokensThisMonth": monthly_tokens,
        "organizationUsedThisMonth": int(
            wallet.get("used_this_month_credits", 0)
        ),
        "totalPurchased": granted,
        "totalConsumed": consumed,
        "totalTokens": tokens,
    }


@router.get("/overview", dependencies=[Depends(require_admin)])
def overview(db: Session = Depends(get_db_no_tenant)) -> dict:
    now = datetime.now(timezone.utc)
    this_month = _month_start(now)
    last_month = _previous_month_start(now)

    total_users = db.query(func.count(User.id)).scalar() or 0
    new_users_this_month = (
        db.query(func.count(User.id)).filter(User.created_at >= this_month).scalar()
        or 0
    )
    new_users_last_month = (
        db.query(func.count(User.id))
        .filter(User.created_at >= last_month, User.created_at < this_month)
        .scalar()
        or 0
    )
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_domains = db.query(func.count(Domain.id)).scalar() or 0
    active_domains = (
        db.query(func.count(Domain.id))
        .filter(Domain.status == DomainStatus.active)
        .scalar()
        or 0
    )
    paid_organizations = (
        db.query(func.count(Organization.id))
        .filter(Organization.plan != "free")
        .scalar()
        or 0
    )

    organizations = db.query(Organization).all()
    wallets = [organization_wallet_snapshot(item) for item in organizations]
    available_credits = sum(item["available_credits"] for item in wallets)
    bonus_credits = sum(item["bonus_credits"] for item in wallets)
    used_this_month = sum(item["used_this_month_credits"] for item in wallets)

    granted_credits = (
        db.query(func.coalesce(func.sum(CreditTransaction.credits_delta), 0))
        .filter(CreditTransaction.credits_delta > 0)
        .scalar()
        or 0
    )
    consumed_credits = (
        db.query(func.coalesce(func.sum(-CreditTransaction.credits_delta), 0))
        .filter(CreditTransaction.credits_delta < 0)
        .scalar()
        or 0
    )
    total_tokens = (
        db.query(
            func.coalesce(
                func.sum(CreditTransaction.tokens_in + CreditTransaction.tokens_out),
                0,
            )
        ).scalar()
        or 0
    )
    total_jobs = db.query(func.count(AiJob.id)).scalar() or 0
    successful_jobs = (
        db.query(func.count(AiJob.id))
        .filter(AiJob.status == JobStatus.success)
        .scalar()
        or 0
    )
    degraded_jobs = (
        db.query(func.count(AiJob.id))
        .filter(AiJob.status == JobStatus.degraded)
        .scalar()
        or 0
    )
    failed_jobs = (
        db.query(func.count(AiJob.id))
        .filter(AiJob.status == JobStatus.failed)
        .scalar()
        or 0
    )

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_projects = (
        db.query(Project, Organization.name)
        .join(Organization, Organization.id == Project.tenant_id)
        .order_by(Project.created_at.desc())
        .limit(5)
        .all()
    )
    db.commit()
    growth = (
        round(
            ((new_users_this_month - new_users_last_month) / new_users_last_month)
            * 100
        )
        if new_users_last_month
        else None
    )
    return {
        "users": {
            "total": int(total_users),
            "new_this_month": int(new_users_this_month),
            "new_last_month": int(new_users_last_month),
            "growth_percent": growth,
        },
        "projects": {"total": int(total_projects)},
        "domains": {"total": int(total_domains), "active": int(active_domains)},
        "subscriptions": {"active": int(paid_organizations)},
        "credits": {
            "available": int(available_credits),
            "bonus": int(bonus_credits),
            "used_this_month": int(used_this_month),
            "granted_total": int(granted_credits),
            "consumed_total": int(consumed_credits),
            "tokens_total": int(total_tokens),
        },
        "jobs": {
            "total": int(total_jobs),
            "success": int(successful_jobs),
            "degraded": int(degraded_jobs),
            "failed": int(failed_jobs),
        },
        "recent_users": [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.full_name or user.email.split("@")[0],
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active,
            }
            for user in recent_users
        ],
        "recent_projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "organization": organization_name,
                "status": project.status.value,
                "created_at": project.created_at.isoformat(),
            }
            for project, organization_name in recent_projects
        ],
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
    monthly_consumed, monthly_tokens = _monthly_usage(db, user.id)
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
            "used_this_month": monthly_consumed,
            "tokens_this_month": monthly_tokens,
            "organization_used_this_month": wallet[
                "used_this_month_credits"
            ],
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
