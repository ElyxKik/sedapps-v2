import uuid

from app.models.billing_plan import BillingPlan
from app.models.payment_receipt import PaymentReceipt
from app.models.user import User
from app.services.invoices import render_invoice_html


def test_invoice_is_branded_and_never_contains_a_license_key():
    user = User(email="client@example.com", password_hash="hash", full_name="Client")
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
    receipt = PaymentReceipt(
        sale_id="sal_123",
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        plan_id=uuid.uuid4(),
        amount_cents=2900,
        currency="EUR",
        status="paid",
    )

    html = render_invoice_html(receipt, user, plan)

    assert "Sala AI" in html
    assert "Facture acquittée" in html
    assert "client@example.com" in html
    assert "29.00 EUR" in html
    assert "license_key" not in html.lower()
