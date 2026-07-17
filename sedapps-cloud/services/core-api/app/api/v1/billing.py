from __future__ import annotations

import hmac
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db, get_current_user, get_db_no_tenant
from app.config import settings
from app.models.billing_plan import BillingPlan
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.user import User
from app.services.invoices import InvoiceDeliveryError, send_payment_invoice

router = APIRouter()
logger = logging.getLogger(__name__)


class CheckoutIn(BaseModel):
    planId: uuid.UUID
    phoneNumber: str = Field(min_length=5, max_length=30, pattern=r"^[0-9]+$")
    countryCode: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    discountCode: str | None = Field(default=None, max_length=100)


_PHONE_RULES: dict[str, tuple[str, int]] = {
    "CD": ("243", 9),
    "CG": ("242", 9),
    "FR": ("33", 9),
    "BE": ("32", 9),
    "CA": ("1", 10),
    "US": ("1", 10),
    "CI": ("225", 10),
    "SN": ("221", 9),
}


def _normalize_phone(number: str, country_code: str) -> str:
    normalized = number.strip()
    if normalized.startswith("00"):
        normalized = normalized[2:]
    rule = _PHONE_RULES.get(country_code.upper())
    if rule is None:
        return normalized.lstrip("0")
    dial_code, national_length = rule
    if normalized.startswith(dial_code) and len(normalized) == (
        len(dial_code) + national_length
    ):
        normalized = normalized[len(dial_code) :]
    if normalized.startswith("0") and len(normalized) == national_length + 1:
        normalized = normalized[1:]
    if len(normalized) != national_length:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Numéro invalide pour {country_code.upper()} : "
            f"{national_length} chiffres nationaux attendus.",
        )
    return normalized


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
        message = _chariow_error_message(body)
        logger.warning(
            "Chariow request rejected: path=%s status=%s message=%s",
            path,
            response.status_code,
            message,
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)
    return body.get("data") or {}


def _chariow_error_message(body: dict) -> str:
    message = body.get("message") or body.get("error")
    if isinstance(message, dict):
        message = message.get("message") or message.get("detail")
    errors = body.get("errors")
    details: list[str] = []
    if isinstance(errors, dict):
        for field, values in errors.items():
            if isinstance(values, list):
                details.extend(f"{field}: {value}" for value in values)
            elif values:
                details.append(f"{field}: {values}")
    elif isinstance(errors, list):
        details.extend(str(value) for value in errors if value)
    parts = [str(message)] if message else []
    parts.extend(details)
    return " · ".join(parts) or "Chariow a refusé les informations de paiement."


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


def _technical_email(tenant_id: uuid.UUID) -> str:
    return f"chariow+{tenant_id}@{settings.CHARIOW_BILLING_EMAIL_DOMAIN}"


def _tenant_from_technical_email(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    local, separator, domain = value.lower().partition("@")
    if separator != "@" or domain != settings.CHARIOW_BILLING_EMAIL_DOMAIN.lower():
        return None
    prefix = "chariow+"
    if not local.startswith(prefix):
        return None
    try:
        return uuid.UUID(local.removeprefix(prefix))
    except ValueError:
        return None


def _amount_cents(sale: dict) -> tuple[int, str]:
    amount = sale.get("amount") or {}
    try:
        cents = int(
            (Decimal(str(amount.get("value", "0"))) * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    except (InvalidOperation, ValueError):
        cents = 0
    return max(0, cents), str(amount.get("currency") or "EUR").upper()[:3]


def _successful_sale(payload: dict, db: Session) -> dict:
    sale = payload.get("sale") or {}
    product = payload.get("product") or {}
    customer = payload.get("customer") or {}
    metadata = sale.get("custom_metadata") or {}
    sale_id = str(sale.get("id") or "")
    if not sale_id or sale.get("status") != "completed":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "invalid sale")
    try:
        tenant_id = uuid.UUID(str(metadata["salaai_org_id"]))
        user_id = uuid.UUID(str(metadata["salaai_user_id"]))
        plan_id = uuid.UUID(str(metadata["salaai_plan_id"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "missing Sala AI checkout metadata",
        ) from exc

    user = db.get(User, user_id)
    organization = db.get(Organization, tenant_id)
    plan = db.get(BillingPlan, plan_id)
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user_id, Membership.org_id == tenant_id)
        .first()
    )
    if not user or not organization or not plan or not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "checkout owner not found")
    if plan.chariow_product_id != product.get("id"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "product mismatch")
    if str(customer.get("email") or "").lower() != _technical_email(tenant_id).lower():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "technical billing email mismatch",
        )

    receipt = (
        db.query(PaymentReceipt).filter(PaymentReceipt.sale_id == sale_id).first()
    )
    if receipt is None:
        amount_cents, currency = _amount_cents(sale)
        receipt = PaymentReceipt(
            sale_id=sale_id,
            tenant_id=tenant_id,
            user_id=user_id,
            plan_id=plan_id,
            amount_cents=amount_cents,
            currency=currency,
            status="paid",
        )
        db.add(receipt)

    organization.plan = plan.slug
    organization.ai_monthly_credit_allowance = plan.monthly_credits
    organization.chariow_customer_id = customer.get("id")
    if organization.chariow_license_status != "active":
        organization.chariow_license_status = "paid_pending_license"
    organization.chariow_license_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(receipt)

    if receipt.invoice_sent_at is None:
        try:
            receipt.resend_email_id = send_payment_invoice(receipt, user, plan)
        except InvoiceDeliveryError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
        receipt.invoice_sent_at = datetime.now(timezone.utc)
        db.commit()
    return {"ok": True, "handled": True, "invoice_sent": True}


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
    phone_number = _normalize_phone(body.phoneNumber, body.countryCode)
    names = (user.full_name or "Client Sala AI").strip().split(maxsplit=1)
    payload: dict[str, Any] = {
        "product_id": plan.chariow_product_id,
        "email": _technical_email(tenant_id),
        "first_name": names[0],
        "last_name": names[1] if len(names) > 1 else "Sala AI",
        "phone": {
            "number": phone_number,
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
    return {
        "plan": organization.plan,
        "status": organization.chariow_license_status,
        "expires_at": organization.chariow_license_expires_at,
        "verified_at": organization.chariow_license_verified_at,
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
    if event == "successful.sale":
        return _successful_sale(payload, db)
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
        technical_tenant_id = _tenant_from_technical_email(customer.get("email"))
        if technical_tenant_id:
            organization = db.get(Organization, technical_tenant_id)

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
