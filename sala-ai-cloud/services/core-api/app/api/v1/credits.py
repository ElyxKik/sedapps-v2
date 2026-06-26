from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.credit import CreditWallet
from app.schemas.credit import CreditEstimateIn, CreditEstimateOut, CreditWalletOut

router = APIRouter()

ESTIMATED_TOKENS = 150_000
MAX_TOKENS = 500_000
CREDITS_PER_1K_TOKENS = 1
ESTIMATED_CREDITS = (ESTIMATED_TOKENS // 1000) * CREDITS_PER_1K_TOKENS
MAX_CREDITS = (MAX_TOKENS // 1000) * CREDITS_PER_1K_TOKENS


def _get_or_create_wallet(db: Session) -> CreditWallet:
    tenant_id = db.info["tenant_id"]
    wallet = (
        db.query(CreditWallet)
        .filter(CreditWallet.tenant_id == tenant_id)
        .first()
    )
    if not wallet:
        wallet = CreditWallet(tenant_id=tenant_id)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


@router.get("/wallet", response_model=CreditWalletOut)
def get_wallet(db: Session = Depends(get_current_org_db)) -> CreditWalletOut:
    wallet = _get_or_create_wallet(db)
    return CreditWalletOut(
        balance_credits=wallet.balance_credits,
        reserved_credits=wallet.reserved_credits,
        available_credits=wallet.balance_credits - wallet.reserved_credits,
        used_this_month_credits=wallet.used_this_month_credits,
        monthly_quota_credits=wallet.monthly_quota_credits,
        plan=wallet.plan,
        reset_at=wallet.reset_at,
    )


@router.post("/estimate", response_model=CreditEstimateOut)
def estimate_credits(
    body: CreditEstimateIn,
    db: Session = Depends(get_current_org_db),
) -> CreditEstimateOut:
    wallet = _get_or_create_wallet(db)
    available = wallet.balance_credits - wallet.reserved_credits
    return CreditEstimateOut(
        estimated_credits=ESTIMATED_CREDITS,
        max_credits=MAX_CREDITS,
        estimated_tokens=ESTIMATED_TOKENS,
        max_tokens=MAX_TOKENS,
        available_credits=available,
        can_start=available >= ESTIMATED_CREDITS,
    )
