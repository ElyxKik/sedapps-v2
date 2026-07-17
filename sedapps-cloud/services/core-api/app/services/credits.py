from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_job import AiJob
from app.models.credit_transaction import CreditTransaction
from app.models.organization import Organization

TOKENS_PER_CREDIT = 1000
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


def _quota(organization: Organization) -> int:
    return max(0, organization.ai_monthly_credit_allowance or 0)


def _balance(organization: Organization) -> int:
    included = max(0, _quota(organization) - max(0, organization.ai_credits_used))
    return included + max(0, organization.ai_bonus_credits or 0)


def _available(organization: Organization) -> int:
    return max(0, _balance(organization) - max(0, organization.ai_credits_reserved))


def _record_transaction(
    db: Session,
    organization: Organization,
    *,
    user_id: uuid.UUID | None,
    transaction_type: str,
    credits_delta: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
    operation: str | None = None,
    description: str | None = None,
    job_id: uuid.UUID | None = None,
    meta: dict | None = None,
) -> CreditTransaction:
    transaction = CreditTransaction(
        tenant_id=organization.id,
        user_id=user_id,
        job_id=job_id,
        type=transaction_type,
        credits_delta=credits_delta,
        balance_after=_available(organization),
        tokens_in=max(0, tokens_in),
        tokens_out=max(0, tokens_out),
        operation=operation,
        description=description,
        meta=meta or {},
    )
    db.add(transaction)
    return transaction


def organization_wallet_snapshot(organization: Organization) -> dict:
    _reset_if_due(organization)
    quota = _quota(organization)
    used = max(0, organization.ai_credits_used)
    reserved = max(0, organization.ai_credits_reserved)
    bonus = max(0, organization.ai_bonus_credits or 0)
    balance = _balance(organization)
    return {
        "balance_credits": balance,
        "reserved_credits": reserved,
        "available_credits": max(0, balance - reserved),
        "used_this_month_credits": used,
        "monthly_quota_credits": quota,
        "bonus_credits": bonus,
        "plan": organization.plan,
        "reset_at": organization.ai_credits_reset_at,
        "tokens_per_credit": TOKENS_PER_CREDIT,
    }


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
    return organization_wallet_snapshot(organization)


def reserve_credits(
    db: Session,
    operation: str,
    tier: str = "standard",
    *,
    tenant_id: uuid.UUID | None = None,
) -> int:
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    available = _available(organization)
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
    user_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
    operation: str | None = None,
    description: str | None = None,
) -> int:
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    organization.ai_credits_reserved = max(
        0, organization.ai_credits_reserved - max(0, reserved)
    )
    charged = credits_for_tokens(max(0, tokens_in) + max(0, tokens_out))
    included_remaining = max(0, _quota(organization) - organization.ai_credits_used)
    bonus_consumed = max(0, charged - included_remaining)
    organization.ai_credits_used += charged
    organization.ai_bonus_credits = max(
        0, (organization.ai_bonus_credits or 0) - bonus_consumed
    )
    if charged:
        _record_transaction(
            db,
            organization,
            user_id=user_id,
            transaction_type="consumption",
            credits_delta=-charged,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            operation=operation,
            description=description or "Consommation IA",
            job_id=job_id,
        )
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
        user_id=job.initiated_by_user_id,
        job_id=job.id,
        operation=job.workflow,
        description=f"Traitement IA : {job.workflow}",
    )
    job.charged_credits = charged
    job.credits_settled = True
    return charged


def grant_bonus_credits(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    credits: int,
    transaction_type: str = "manual",
    description: str | None = None,
) -> CreditTransaction:
    if credits <= 0:
        raise ValueError("credits must be greater than zero")
    if transaction_type not in {"manual", "promotion", "purchase", "refund"}:
        raise ValueError("invalid credit transaction type")
    organization = _lock_organization(db, tenant_id)
    _reset_if_due(organization)
    organization.ai_bonus_credits = max(0, organization.ai_bonus_credits or 0) + credits
    return _record_transaction(
        db,
        organization,
        user_id=user_id,
        transaction_type=transaction_type,
        credits_delta=credits,
        description=description or "Crédits ajoutés par un administrateur",
        meta={"source": "sedadmin"},
    )
