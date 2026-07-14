from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class DeployClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = base_url or settings.DEPLOY_SERVICE_URL
        self.token = token or settings.INTERNAL_API_TOKEN

    async def enqueue_site_deployment(
        self,
        *,
        deployment_id: str,
        tenant_id: str,
        project_id: str,
        site_version_id: str,
        slug: str,
        payload: dict[str, Any],
        custom_domain: str | None = None,
    ) -> None:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                f"{self.base_url}/v1/deployments/site",
                headers={"X-Internal-Token": self.token},
                json={
                    "deployment_id": deployment_id,
                    "tenant_id": tenant_id,
                    "project_id": project_id,
                    "site_version_id": site_version_id,
                    "slug": slug,
                    "custom_domain": custom_domain,
                    "payload": payload,
                },
            )
            r.raise_for_status()
