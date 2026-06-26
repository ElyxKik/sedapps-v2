from __future__ import annotations

import ovh

from app.config import settings


class OvhDnsClient:
    def __init__(self) -> None:
        self.zone = settings.OVH_ZONE_NAME
        self._client = None
        if not settings.DEPLOY_DRY_RUN:
            self._client = ovh.Client(
                endpoint=settings.OVH_ENDPOINT,
                application_key=settings.OVH_APP_KEY,
                application_secret=settings.OVH_APP_SECRET,
                consumer_key=settings.OVH_CONSUMER_KEY,
            )

    def upsert_cname(self, subdomain: str, target: str) -> dict[str, str | int]:
        if settings.DEPLOY_DRY_RUN:
            return {"dry_run": 1, "type": "CNAME", "subdomain": subdomain, "target": target}
        if self._client is None:
            raise RuntimeError("OVH client not initialized")

        ids = self._client.get(
            f"/domain/zone/{self.zone}/record",
            fieldType="CNAME",
            subDomain=subdomain,
        )
        for record_id in ids:
            self._client.delete(f"/domain/zone/{self.zone}/record/{record_id}")

        record = self._client.post(
            f"/domain/zone/{self.zone}/record",
            fieldType="CNAME",
            subDomain=subdomain,
            target=target.rstrip(".") + ".",
            ttl=300,
        )
        self._client.post(f"/domain/zone/{self.zone}/refresh")
        return {"dry_run": 0, "record_id": record.get("id", 0), "subdomain": subdomain, "target": target}

    def upsert_txt(self, subdomain: str, value: str) -> dict[str, str | int]:
        if settings.DEPLOY_DRY_RUN:
            return {"dry_run": 1, "type": "TXT", "subdomain": subdomain, "value": value}
        if self._client is None:
            raise RuntimeError("OVH client not initialized")

        ids = self._client.get(
            f"/domain/zone/{self.zone}/record",
            fieldType="TXT",
            subDomain=subdomain,
        )
        for record_id in ids:
            self._client.delete(f"/domain/zone/{self.zone}/record/{record_id}")

        record = self._client.post(
            f"/domain/zone/{self.zone}/record",
            fieldType="TXT",
            subDomain=subdomain,
            target=f'"{value}"',
            ttl=60,
        )
        self._client.post(f"/domain/zone/{self.zone}/refresh")
        return {"dry_run": 0, "record_id": record.get("id", 0), "subdomain": subdomain}
