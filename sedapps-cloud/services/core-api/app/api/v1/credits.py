from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.services.credits import TOKENS_PER_CREDIT, estimated_credits, wallet_snapshot

router = APIRouter()

class EstimateIn(BaseModel):
    operation: str = "site_generation"
    tier: str = "standard"


@router.get("/wallet")
def wallet(db: Session = Depends(get_current_org_db)) -> dict:
    return wallet_snapshot(db)


@router.post("/estimate")
def estimate(body: EstimateIn, db: Session = Depends(get_current_org_db)) -> dict:
    wallet_data = wallet_snapshot(db)
    estimated = estimated_credits(body.operation, body.tier)
    maximum = max(estimated, round(estimated * 1.5))
    available = wallet_data["available_credits"]
    return {
        "operation": body.operation,
        "tier": body.tier,
        "estimated_credits": estimated,
        "max_credits": maximum,
        "estimated_tokens": estimated * TOKENS_PER_CREDIT,
        "max_tokens": maximum * TOKENS_PER_CREDIT,
        "tokens_per_credit": TOKENS_PER_CREDIT,
        "available_credits": available,
        "can_start": available >= estimated,
    }
