from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_job import AiJob
from app.models.organization import Organization

TOKENS_PER_CREDIT = 1000
PLAN_QUOTAS = {"free": 500, "starter": 2500, "pro": 10000, "business": 50000}
OPERATION_COSTS = {
    "site_generation": {"standard": 250, "premium": 500},
    "site_edit": {"standard": 10, "premium": 25},
    "article_generation": {"standard": 40, "premium": 80},
}


class InsufficientCreditsError(ValueError):
    def __init__(self, required: int, available: int) -> None:
        self.required = required
        self.available = available
        super().__init__(f"{required} credits required, {available} available")


def credits_for_tokens(tokens: int) -> int:
    """Bill whole credits, rounding any partial 1,000-token block upward."""
    return math.ceil(max(0, tokens) / TOKENS_PER_CREDIT)


def estimated_credits(operation: str, tier: str = "standard") -> int:
    costs = OPERATION_COSTS.get(operation, {"standard": 25})
    return int(costs.get(tier, costs.get("standard", 25)))


def _next_month(now: datetime) -> datetime:
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    return datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)


def _lock_organization(db: Session, tenant_id: uuid.UUID | None = None) -> Organization:
    organization_id = tenant_id or db.info.get("tenant_id")
    organization = db.execute(
        select(Organization)
        .where(Organization.id == organization_id)
        .with_for_update()
    ).scalar_one_or_none()
    if organization is None:
        raise ValueError("organization not found")
    return organization


def _reset_if_due(organization: Organization, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    reset_at = organization.ai_credits_reset_at
    if reset_at is None:
        organization.ai_credits_reset_at = _next_month(current)
        return True
    if reset_at <= current:
        organization.ai_credits_used = 0
        organization.ai_credits_reserved = 0
        organization.ai_credits_reset_at = _next_month(current)
        return True
    return False


def wallet_snapshot(db: Session, *, lock: bool = False) -> dict:
    tenant_id = db.info.get("tenant_id")
    if lock:
        organization = _lock_organization(db, tenant_id)
    else:
        organization = db.get(Organization, tenant_id)
        if organization is None:
            raise ValueError("organization not found")
    changed = _reset_if_due(organization)
    if changed:
        db.commit()
        if lock:
            organization = _lock_organization(db, tenant_id)
        else:
            db.refresh(organization)
    quota = PLAN_QUOTAS.get(organization.plan, PLAN_QUOTAS["free"])
    used = max(0, organization.ai_credits_used)
    reserved = max(0, organization.ai_credits_reserved)
    balance = max(0, quota - used)
    return {
        "balance_credits": balance,
        "reserved_credits": reserved,
        "available_credits": max(0, balance - reserved),
        "used_this_month_credits": used,
        "monthly_quota_credits": quota,
        "plan": organization.plan,
        "reset_at": organization.ai_credits_reset_at,
        "tokens_per_credit": TOKENS_PER_CREDIT,
    }


def reserve_credits(
    db: Session,
    operation: str,
    tier: str = "standard",
    *,
    tenant_id: uuid.UUID | None = None,
) -> int:
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    quota = PLAN_QUOTAS.get(organization.plan, PLAN_QUOTAS["free"])
    available = max(
        0,
        quota - organization.ai_credits_used - organization.ai_credits_reserved,
    )
    required = estimated_credits(operation, tier)
    if available < required:
        raise InsufficientCreditsError(required, available)
    organization.ai_credits_reserved += required
    return required


def settle_reserved_credits(
    db: Session,
    reserved: int,
    tokens_in: int,
    tokens_out: int,
    *,
    tenant_id: uuid.UUID | None = None,
) -> int:
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    organization.ai_credits_reserved = max(
        0, organization.ai_credits_reserved - max(0, reserved)
    )
    charged = credits_for_tokens(max(0, tokens_in) + max(0, tokens_out))
    organization.ai_credits_used += charged
    return charged


def release_reserved_credits(
    db: Session, reserved: int, *, tenant_id: uuid.UUID | None = None
) -> None:
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    organization.ai_credits_reserved = max(
        0, organization.ai_credits_reserved - max(0, reserved)
    )


def settle_job_credits(db: Session, job: AiJob) -> int:
    if job.credits_settled:
        return job.charged_credits
    charged = settle_reserved_credits(
        db,
        job.reserved_credits,
        job.tokens_in,
        job.tokens_out,
        tenant_id=job.tenant_id,
    )
    job.charged_credits = charged
    job.credits_settled = True
    return charged
