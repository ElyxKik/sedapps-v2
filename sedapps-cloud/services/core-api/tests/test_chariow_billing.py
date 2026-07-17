from datetime import datetime, timezone

from app.api.v1.billing import _apply_active_license, _downgrade_license
from app.models.billing_plan import BillingPlan
from app.models.organization import Organization


def test_active_chariow_license_applies_plan_and_monthly_credits():
    organization = Organization(
        name="Acme",
        plan="free",
        ai_monthly_credit_allowance=50,
    )
    plan = BillingPlan(
        slug="pro",
        name="Pro",
        billing_interval="month",
        price_cents=2900,
        currency="EUR",
        monthly_credits=500,
        is_active=True,
        sort_order=10,
    )

    _apply_active_license(
        organization,
        plan,
        {
            "id": "lic_123",
            "status": "active",
            "license": {"key": "SALA-PRO-1234"},
            "expires_at": "2026-08-17T00:00:00Z",
        },
        {"id": "cus_123"},
    )

    assert organization.plan == "pro"
    assert organization.ai_monthly_credit_allowance == 500
    assert organization.chariow_license_id == "lic_123"
    assert organization.chariow_license_key == "SALA-PRO-1234"
    assert organization.chariow_customer_id == "cus_123"
    assert organization.chariow_license_expires_at == datetime(
        2026, 8, 17, tzinfo=timezone.utc
    )


def test_expired_license_returns_to_free_without_losing_bonus_credits():
    organization = Organization(
        name="Acme",
        plan="pro",
        ai_monthly_credit_allowance=500,
        ai_bonus_credits=75,
        ai_credits_reserved=12,
    )

    _downgrade_license(organization, "expired")

    assert organization.plan == "free"
    assert organization.ai_monthly_credit_allowance == 50
    assert organization.ai_bonus_credits == 75
    assert organization.ai_credits_reserved == 0
    assert organization.chariow_license_status == "expired"
