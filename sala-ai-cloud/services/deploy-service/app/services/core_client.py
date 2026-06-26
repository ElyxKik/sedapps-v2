from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class CoreApiClient:
    def __init__(self) -> None:
        self.base = settings.CORE_API_URL.rstrip("/")
        self.headers = {"X-Internal-Token": settings.INTERNAL_API_TOKEN}

    def deployment_update(self, deployment_id: str, payload: dict[str, Any]) -> None:
        url = f"{self.base}/v1/internal/deployments/{deployment_id}"
        try:
            r = httpx.post(url, json=payload, headers=self.headers, timeout=20)
            if r.status_code == 404:
                return
            r.raise_for_status()
        except Exception:
            return
