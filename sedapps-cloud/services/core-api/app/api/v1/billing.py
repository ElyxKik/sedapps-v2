from __future__ import annotations

import hmac
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db, get_current_user, get_db_no_tenant
from app.config import settings
from app.models.billing_plan import BillingPlan
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User

router = APIRouter()


class CheckoutIn(BaseModel):
    planId: uuid.UUID
    phoneNumber: str = Field(min_length=5, max_length=30, pattern=r"^[0-9]+$")
    countryCode: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    discountCode: str | None = Field(default=None, max_length=100)


class ActivateLicenseIn(BaseModel):
    licenseKey: str = Field(min_length=8, max_length=255)


def _require_chariow() -> None:
    if not settings.CHARIOW_API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Chariow is not configured",
        )


def _chariow(method: str, path: str, *, payload: dict | None = None) -> dict:
    _require_chariow()
    try:
        response = httpx.request(
            method,
            f"{settings.CHARIOW_API_URL.rstrip('/')}/{path.lstrip('/')}",
            headers={
                "Authorization": f"Bearer {settings.CHARIOW_API_KEY}",
                "Accept": "application/json",
            },
            json=payload,
            timeout=20,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Chariow is temporarily unreachable",
        ) from exc
    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.status_code >= 400:
        message = body.get("message") or "Chariow rejected the request"
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)
    return body.get("data") or {}


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _license_key(data: dict) -> str | None:
    nested = data.get("license")
    if isinstance(nested, dict):
        return nested.get("key")
    return data.get("key")


def _plan_for_product(db: Session, product_id: str | None) -> BillingPlan | None:
    if not product_id:
        return None
    return (
        db.query(BillingPlan)
        .filter(
            BillingPlan.chariow_product_id == product_id,
            BillingPlan.is_active.is_(True),
        )
        .first()
    )


def _apply_active_license(
    organization: Organization,
    plan: BillingPlan,
    license_data: dict,
    customer: dict | None = None,
) -> None:
    organization.plan = plan.slug
    organization.ai_monthly_credit_allowance = plan.monthly_credits
    organization.chariow_license_id = license_data.get("id")
    organization.chariow_license_key = _license_key(license_data)
    organization.chariow_license_status = license_data.get("status") or "active"
    organization.chariow_license_expires_at = _parse_date(
        license_data.get("expires_at")
    )
    organization.chariow_license_verified_at = datetime.now(timezone.utc)
    if customer:
        organization.chariow_customer_id = customer.get("id")


def _downgrade_license(organization: Organization, status_value: str) -> None:
    organization.plan = "free"
    organization.ai_monthly_credit_allowance = 50
    organization.ai_credits_reserved = 0
    organization.chariow_license_status = status_value
    organization.chariow_license_verified_at = datetime.now(timezone.utc)


@router.get("/plans")
def public_plans(db: Session = Depends(get_current_org_db)) -> dict:
    plans = (
        db.query(BillingPlan)
        .filter(BillingPlan.is_active.is_(True))
        .order_by(BillingPlan.sort_order.asc(), BillingPlan.price_cents.asc())
        .all()
    )
    return {
        "plans": [
            {
                "id": str(plan.id),
                "slug": plan.slug,
                "name": plan.name,
                "description": plan.description,
                "billing_interval": plan.billing_interval,
                "price_cents": plan.price_cents,
                "currency": plan.currency,
                "monthly_credits": plan.monthly_credits,
                "checkout_enabled": bool(
                    plan.chariow_product_id and settings.CHARIOW_API_KEY
                ),
            }
            for plan in plans
        ]
    }


@router.post("/checkout")
def create_checkout(
    body: CheckoutIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_current_org_db),
) -> dict:
    plan = db.get(BillingPlan, body.planId)
    if plan is None or not plan.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "plan not found")
    if plan.slug == "free" or not plan.chariow_product_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "this plan is not linked to a Chariow license product",
        )
    tenant_id = db.info["tenant_id"]
    names = (user.full_name or "Client Sala AI").strip().split(maxsplit=1)
    payload: dict[str, Any] = {
        "product_id": plan.chariow_product_id,
        "email": user.email,
        "first_name": names[0],
        "last_name": names[1] if len(names) > 1 else "Sala AI",
        "phone": {
            "number": body.phoneNumber,
            "country_code": body.countryCode.upper(),
        },
        "redirect_url": "https://app.salaai.site/#/account?payment=success",
        "custom_metadata": {
            "salaai_user_id": str(user.id),
            "salaai_org_id": str(tenant_id),
            "salaai_plan_id": str(plan.id),
        },
    }
    if body.discountCode:
        payload["discount_code"] = body.discountCode
    data = _chariow("POST", "/checkout", payload=payload)
    payment = data.get("payment") or {}
    return {
        "step": data.get("step"),
        "checkout_url": payment.get("checkout_url"),
        "purchase_id": (data.get("purchase") or {}).get("id"),
    }


@router.get("/license")
def current_license(db: Session = Depends(get_current_org_db)) -> dict:
    organization = db.get(Organization, db.info["tenant_id"])
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    key = organization.chariow_license_key or ""
    return {
        "plan": organization.plan,
        "status": organization.chariow_license_status,
        "masked_key": f"***-{key[-4:]}" if key else None,
        "expires_at": organization.chariow_license_expires_at,
        "verified_at": organization.chariow_license_verified_at,
    }


@router.post("/license/activate")
def activate_license(
    body: ActivateLicenseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_current_org_db),
) -> dict:
    key = body.licenseKey.strip()
    encoded_key = quote(key, safe="")
    data = _chariow("GET", f"/licenses/{encoded_key}")
    customer = data.get("customer") or {}
    product = data.get("product") or {}
    if str(customer.get("email", "")).lower() != user.email.lower():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "this license belongs to another customer",
        )
    plan = _plan_for_product(db, product.get("id"))
    if plan is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "this Chariow product is not linked to a Sala AI plan",
        )
    if data.get("status") == "pending_activation":
        _chariow(
            "POST",
            f"/licenses/{encoded_key}/activate",
            payload={"device_identifier": f"salaai-org:{db.info['tenant_id']}"},
        )
        data = _chariow("GET", f"/licenses/{encoded_key}")
    if not data.get("is_active") or data.get("is_expired"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "the Chariow license is inactive or expired",
        )
    organization = db.get(Organization, db.info["tenant_id"])
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "organization not found")
    _apply_active_license(organization, plan, data, customer)
    db.commit()
    return {
        "ok": True,
        "plan": plan.slug,
        "monthly_credits": plan.monthly_credits,
        "status": organization.chariow_license_status,
        "expires_at": organization.chariow_license_expires_at,
    }


@router.post("/chariow/pulse")
def chariow_pulse(
    payload: dict,
    token: str = Query(default=""),
    db: Session = Depends(get_db_no_tenant),
) -> dict:
    if not settings.CHARIOW_PULSE_SECRET or not hmac.compare_digest(
        token, settings.CHARIOW_PULSE_SECRET
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid pulse secret")
    event = str(payload.get("event") or "")
    license_data = payload.get("license") or {}
    customer = payload.get("customer") or {}
    product = payload.get("product") or {}
    license_id = license_data.get("id")
    license_key = _license_key(license_data)

    organization = None
    if license_id:
        organization = (
            db.query(Organization)
            .filter(Organization.chariow_license_id == license_id)
            .first()
        )
    if organization is None and customer.get("email"):
        user = (
            db.query(User)
            .filter(User.email.ilike(str(customer["email"])))
            .first()
        )
        if user:
            membership = (
                db.query(Membership)
                .filter(Membership.user_id == user.id)
                .order_by(Membership.created_at.asc())
                .first()
            )
            organization = db.get(Organization, membership.org_id) if membership else None

    if organization is None:
        return {"ok": True, "handled": False}

    if event in {"license.issued", "license.activated"}:
        plan = _plan_for_product(db, product.get("id"))
        if plan is None:
            return {"ok": True, "handled": False}
        organization.chariow_license_id = license_id
        organization.chariow_license_key = license_key
        organization.chariow_license_status = license_data.get("status")
        organization.chariow_license_expires_at = _parse_date(
            license_data.get("expires_at")
        )
        organization.chariow_customer_id = customer.get("id")
        if event == "license.activated" or license_data.get("status") == "active":
            _apply_active_license(organization, plan, license_data, customer)
    elif event in {"license.expired", "license.revoked"}:
        _downgrade_license(organization, event.removeprefix("license."))
    else:
        return {"ok": True, "handled": False}

    db.commit()
    return {"ok": True, "handled": True}
