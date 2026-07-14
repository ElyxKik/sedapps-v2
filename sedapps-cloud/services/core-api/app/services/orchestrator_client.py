from __future__ import annotations

import httpx

from app.config import settings


class OrchestratorClient:
    """Thin async HTTP client to talk to the ai-orchestrator service."""

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = base_url or settings.AI_ORCHESTRATOR_URL
        self.token = token or settings.INTERNAL_API_TOKEN

    async def enqueue_site_generation(
        self, *, job_id: str, project_id: str, tenant_id: str, brief: dict, locale: str = "fr"
    ) -> None:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                f"{self.base_url}/v1/workflows/site-generation",
                headers={"X-Internal-Token": self.token},
                json={
                    "job_id": job_id,
                    "project_id": project_id,
                    "tenant_id": tenant_id,
                    "brief": brief,
                    "locale": locale,
                },
            )
            r.raise_for_status()

    async def enqueue_article_generation(
        self, *, job_id: str, project_id: str, tenant_id: str, params: dict
    ) -> None:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                f"{self.base_url}/v1/workflows/article-generation",
                headers={"X-Internal-Token": self.token},
                json={
                    "job_id": job_id,
                    "project_id": project_id,
                    "tenant_id": tenant_id,
                    "params": params,
                },
            )
            r.raise_for_status()

    async def run_agent(
        self,
        name: str,
        *,
        project_id: str,
        tenant_id: str,
        context: dict,
        params: dict,
    ) -> dict:
        async with httpx.AsyncClient(timeout=130.0) as c:
            response = await c.post(
                f"{self.base_url}/v1/agents/{name}/run",
                headers={"X-Internal-Token": self.token},
                json={
                    "project_id": project_id,
                    "tenant_id": tenant_id,
                    "context": context,
                    "params": params,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", payload)
