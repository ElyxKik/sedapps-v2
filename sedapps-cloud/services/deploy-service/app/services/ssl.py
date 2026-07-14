from __future__ import annotations

from app.config import settings
from app.services.ovh_dns import OvhDnsClient


def prepare_dns01_challenge(domain: str, token_value: str) -> dict[str, str | int]:
    subdomain = f"_acme-challenge.{domain.replace('.' + settings.OVH_ZONE_NAME, '')}"
    return OvhDnsClient().upsert_txt(subdomain=subdomain, value=token_value)
