"""HTTP client used by the orchestrator/agents to call core-api back."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class CoreApiClient:
    def __init__(self) -> None:
        self.base = settings.CORE_API_URL.rstrip("/")
        self.headers = {"X-Internal-Token": settings.INTERNAL_API_TOKEN}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as c:
            r = c.post(f"{self.base}{path}", headers=self.headers, json=payload)
            r.raise_for_status()
            return r.json()

    def job_start(self, job_id: str) -> None:
        self._post(f"/v1/internal/jobs/{job_id}/start", {})

    def record_event(self, job_id: str, event: dict[str, Any]) -> None:
        self._post(f"/v1/internal/jobs/{job_id}/events", event)

    def record_run(self, job_id: str, run: dict[str, Any]) -> None:
        self._post(f"/v1/internal/jobs/{job_id}/agent-runs", run)

    def job_complete(self, job_id: str, body: dict[str, Any]) -> None:
        self._post(f"/v1/internal/jobs/{job_id}/complete", body)
