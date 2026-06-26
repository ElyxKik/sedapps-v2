from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreditWalletOut(BaseModel):
    balance_credits: int
    reserved_credits: int
    available_credits: int
    used_this_month_credits: int
    monthly_quota_credits: int
    plan: str
    reset_at: datetime | None

    model_config = {"from_attributes": True}


class CreditEstimateIn(BaseModel):
    operation: str = "site_generation"
    tier: str = "standard"


class CreditEstimateOut(BaseModel):
    estimated_credits: int
    max_credits: int
    estimated_tokens: int
    max_tokens: int
    available_credits: int
    can_start: bool


class CreditTransactionOut(BaseModel):
    id: UUID
    project_id: UUID | None
    job_id: UUID | None
    type: str
    status: str
    credits: int
    tokens: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}
