from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import quote

import dns.resolver
import httpx
import ovh

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainAvailability:
    available: bool
    checked: bool
    source: str
    message: str


class OvhClient:
    """Domain lookup with OVH when configured, then public RDAP as fallback."""

    def __init__(self) -> None:
        self.enabled = bool(
            settings.OVH_APP_KEY and settings.OVH_APP_SECRET and settings.OVH_CONSUMER_KEY
        )
        self._client = None
        if self.enabled:
            try:
                self._client = ovh.Client(
                    endpoint=settings.OVH_ENDPOINT,
                    application_key=settings.OVH_APP_KEY,
                    application_secret=settings.OVH_APP_SECRET,
                    consumer_key=settings.OVH_CONSUMER_KEY,
                )
            except Exception:
                logger.exception("Unable to initialize OVH domain client")
                self.enabled = False

    def availability(self, domain: str) -> DomainAvailability:
        if self._client:
            try:
                results = self._client.get("/domain/register/search", domain=domain)
                for item in results:
                    if item.get("domain") == domain:
                        available = item.get("action") == "create"
                        return DomainAvailability(
                            available=available,
                            checked=True,
                            source="ovh",
                            message="Disponible à l’enregistrement." if available else "Déjà enregistré.",
                        )
            except Exception:
                logger.exception("OVH domain lookup failed for %s", domain)
        return self._rdap_availability(domain)

    @staticmethod
    def _rdap_availability(domain: str) -> DomainAvailability:
        try:
            response = httpx.get(
                f"https://rdap.org/domain/{quote(domain)}",
                follow_redirects=True,
                timeout=6.0,
                headers={"Accept": "application/rdap+json"},
            )
            if response.status_code == 404:
                return DomainAvailability(True, True, "rdap", "Disponible à l’enregistrement.")
            if response.status_code == 200:
                return DomainAvailability(False, True, "rdap", "Déjà enregistré.")
            logger.warning("RDAP lookup returned %s for %s", response.status_code, domain)
        except httpx.HTTPError:
            logger.exception("RDAP domain lookup failed for %s", domain)
        return DomainAvailability(
            False,
            False,
            "rdap",
            "La disponibilité n’a pas pu être vérifiée. Réessaie dans un instant.",
        )

    @staticmethod
    def has_verification_record(name: str, value: str) -> bool:
        try:
            records = dns.resolver.resolve(name, "TXT", lifetime=8.0)
            expected = value.replace('"', "")
            return any(
                "".join(part.decode() if isinstance(part, bytes) else str(part) for part in record.strings)
                .replace('"', "")
                == expected
                for record in records
            )
        except (dns.resolver.DNSException, OSError):
            return False
