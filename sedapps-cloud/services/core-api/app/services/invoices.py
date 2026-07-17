from __future__ import annotations

from datetime import datetime, timezone
from html import escape

import httpx

from app.config import settings
from app.models.billing_plan import BillingPlan
from app.models.payment_receipt import PaymentReceipt
from app.models.user import User


class InvoiceDeliveryError(RuntimeError):
    pass


def _money(cents: int, currency: str) -> str:
    return f"{cents / 100:,.2f} {currency}".replace(",", " ")


def render_invoice_html(
    receipt: PaymentReceipt,
    user: User,
    plan: BillingPlan,
) -> str:
    invoice_number = f"SALA-{receipt.sale_id.upper()}"
    paid_at = (receipt.created_at or datetime.now(timezone.utc)).strftime("%d/%m/%Y")
    interval = "annuel" if plan.billing_interval == "year" else "mensuel"
    legal_lines = "<br>".join(
        escape(value)
        for value in [settings.SALAAI_LEGAL_ADDRESS, settings.SALAAI_TAX_ID]
        if value
    )
    return f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;background:#071426;font-family:Inter,Arial,sans-serif;color:#eaf2ff">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#071426;padding:32px 12px">
      <tr><td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;background:#0c1d35;border:1px solid #1f3655;border-radius:24px;overflow:hidden">
          <tr><td style="padding:30px;background:linear-gradient(135deg,#102f62,#0c1d35)">
            <table role="presentation" width="100%"><tr>
              <td><img src="{escape(settings.SALAAI_INVOICE_LOGO_URL)}" width="58" height="58" alt="Sala AI" style="display:block;border-radius:15px"></td>
              <td align="right"><div style="font-size:12px;letter-spacing:2px;color:#7fb4ff;text-transform:uppercase">Facture acquittée</div><div style="margin-top:7px;font-size:13px;color:#91a6c2">{escape(invoice_number)}</div></td>
            </tr></table>
          </td></tr>
          <tr><td style="padding:32px">
            <h1 style="margin:0 0 8px;font-size:26px;color:#ffffff">Merci pour votre confiance.</h1>
            <p style="margin:0 0 28px;line-height:1.6;color:#9eb0c8">Votre paiement a été confirmé. Votre plan Sala AI est désormais associé à votre compte, sans aucune clé de licence à saisir.</p>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:26px">
              <tr>
                <td style="padding:16px;background:#0a172a;border-radius:14px;color:#91a6c2;font-size:13px;line-height:1.7"><strong style="color:#ffffff">Facturé à</strong><br>{escape(user.full_name or user.email)}<br>{escape(user.email)}</td>
                <td width="14"></td>
                <td style="padding:16px;background:#0a172a;border-radius:14px;color:#91a6c2;font-size:13px;line-height:1.7"><strong style="color:#ffffff">Émis par</strong><br>{escape(settings.SALAAI_LEGAL_NAME)}{('<br>' + legal_lines) if legal_lines else ''}</td>
              </tr>
            </table>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
              <tr style="color:#7d92ad;font-size:12px;text-transform:uppercase;letter-spacing:1px"><td style="padding:12px;border-bottom:1px solid #233957">Description</td><td align="right" style="padding:12px;border-bottom:1px solid #233957">Montant</td></tr>
              <tr><td style="padding:20px 12px;border-bottom:1px solid #233957"><strong style="color:#ffffff">Plan {escape(plan.name)}</strong><br><span style="font-size:13px;color:#7d92ad">Facturation {interval} · {plan.monthly_credits:,} crédits/mois</span></td><td align="right" style="padding:20px 12px;border-bottom:1px solid #233957;font-weight:700;color:#ffffff">{escape(_money(receipt.amount_cents, receipt.currency))}</td></tr>
              <tr><td style="padding:20px 12px;color:#8da2bd">Payé le {paid_at}</td><td align="right" style="padding:20px 12px;font-size:22px;font-weight:800;color:#60a5fa">{escape(_money(receipt.amount_cents, receipt.currency))}</td></tr>
            </table>
            <div style="margin-top:22px;padding:16px;border-radius:14px;background:#0a172a;color:#8da2bd;font-size:12px;line-height:1.6">Référence Chariow : {escape(receipt.sale_id)}<br>Conservez cet email comme justificatif de paiement.</div>
          </td></tr>
          <tr><td align="center" style="padding:22px;border-top:1px solid #1f3655;color:#667d99;font-size:12px">Sala AI · Création de sites web assistée par intelligence artificielle</td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
""".strip()


def send_payment_invoice(
    receipt: PaymentReceipt,
    user: User,
    plan: BillingPlan,
) -> str:
    if not settings.RESEND_API_KEY:
        raise InvoiceDeliveryError("Resend is not configured")
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
                "Idempotency-Key": f"salaai-invoice-{receipt.sale_id}"[:256],
            },
            json={
                "from": settings.RESEND_FROM_EMAIL,
                "to": [user.email],
                "subject": f"Facture Sala AI · Plan {plan.name}",
                "html": render_invoice_html(receipt, user, plan),
                "tags": [
                    {"name": "type", "value": "payment_invoice"},
                    {"name": "provider", "value": "chariow"},
                ],
            },
            timeout=20,
        )
    except httpx.RequestError as exc:
        raise InvoiceDeliveryError("Resend is temporarily unreachable") from exc
    if response.status_code >= 400:
        raise InvoiceDeliveryError(f"Resend rejected the invoice ({response.status_code})")
    try:
        email_id = response.json().get("id")
    except ValueError as exc:
        raise InvoiceDeliveryError("Resend returned an invalid response") from exc
    if not email_id:
        raise InvoiceDeliveryError("Resend did not return an email ID")
    return str(email_id)
