import pytest
from pydantic import ValidationError

from app.api.v1.admin import BillingPlanIn, _apply_plan
from app.models.billing_plan import BillingPlan


def test_admin_can_define_a_monthly_plan():
    plan = BillingPlan()
    body = BillingPlanIn(
        slug="starter",
        name="Starter",
        billingInterval="month",
        priceCents=900,
        monthlyCredits=250,
        chariowProductId="prd_starter",
    )

    _apply_plan(plan, body)

    assert plan.billing_interval == "month"
    assert plan.price_cents == 900
    assert plan.monthly_credits == 250
    assert plan.currency == "EUR"


def test_admin_can_define_an_annual_plan_with_monthly_credits():
    plan = BillingPlan()
    body = BillingPlanIn(
        slug="pro",
        name="Pro annuel",
        billingInterval="year",
        priceCents=29000,
        currency="usd",
        monthlyCredits=1000,
        chariowProductId="prd_annual",
    )

    _apply_plan(plan, body)

    assert plan.billing_interval == "year"
    assert plan.price_cents == 29000
    assert plan.currency == "USD"
    assert plan.monthly_credits == 1000
    assert plan.chariow_product_id == "prd_annual"


def test_paid_plan_requires_a_chariow_license_product():
    with pytest.raises(ValidationError):
        BillingPlanIn(
            slug="pro",
            name="Pro",
            billingInterval="month",
            priceCents=2900,
            monthlyCredits=500,
        )
