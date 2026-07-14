from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.organization import Organization

router = APIRouter()

PLAN_QUOTAS = {"free": 500, "starter": 2500, "pro": 10000, "business": 50000}
OPERATION_COSTS = {
    "site_generation": {"standard": 250, "premium": 500},
    "site_edit": {"standard": 10, "premium": 25},
    "article_generation": {"standard": 40, "premium": 80},
}


class EstimateIn(BaseModel):
    operation: str = "site_generation"
    tier: str = "standard"


def _wallet(db: Session) -> dict:
    organization = db.get(Organization, db.info["tenant_id"])
    plan = organization.plan if organization else "free"
    quota = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    return {
        "balance_credits": quota,
        "reserved_credits": 0,
        "available_credits": quota,
        "used_this_month_credits": 0,
        "monthly_quota_credits": quota,
        "plan": plan,
        "reset_at": None,
    }


@router.get("/wallet")
def wallet(db: Session = Depends(get_current_org_db)) -> dict:
    return _wallet(db)


@router.post("/estimate")
def estimate(body: EstimateIn, db: Session = Depends(get_current_org_db)) -> dict:
    wallet_data = _wallet(db)
    costs = OPERATION_COSTS.get(body.operation, {"standard": 25})
    estimated = costs.get(body.tier, costs.get("standard", 25))
    maximum = max(estimated, round(estimated * 1.5))
    available = wallet_data["available_credits"]
    return {
        "operation": body.operation,
        "tier": body.tier,
        "estimated_credits": estimated,
        "max_credits": maximum,
        "estimated_tokens": estimated * 1000,
        "max_tokens": maximum * 1000,
        "available_credits": available,
        "can_start": available >= estimated,
    }
