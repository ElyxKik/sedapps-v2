from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agents import AgentInput, BlogWriterAgent
from app.celery_app import celery
from app.core_client import CoreApiClient

log = logging.getLogger(__name__)


async def _orchestrate(
    job_id: str, project_id: str, tenant_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    core = CoreApiClient()
    core.job_start(job_id)
    inp = AgentInput(
        project_id=project_id,
        job_id=job_id,
        tenant_id=tenant_id,
        locale=params.get("locale", "fr"),
        context={"brief": params.get("brief", {})},
        params=params,
    )
    out = await BlogWriterAgent().run(inp)
    core.record_run(
        job_id,
        {
            "agent_name": out.agent,
            "model": out.model,
            "status": out.status,
            "duration_ms": out.duration_ms,
            "tokens_in": out.tokens.prompt,
            "tokens_out": out.tokens.completion,
            "input": params,
            "output": out.data,
            "warnings": out.warnings,
        },
    )
    core.job_complete(
        job_id,
        {
            "status": "success" if out.status == "ok" else "degraded",
            "error": None,
            "output": {"article": out.data},
            "tokens_in": out.tokens.prompt,
            "tokens_out": out.tokens.completion,
        },
    )
    return out.data


@celery.task(name="workflows.article_generation", bind=True, max_retries=1)
def run_article_generation(
    self, job_id: str, project_id: str, tenant_id: str, params: dict[str, Any]
) -> dict[str, Any]:
    log.info("article_generation start job=%s", job_id)
    try:
        return asyncio.run(_orchestrate(job_id, project_id, tenant_id, params))
    except Exception as e:  # noqa: BLE001
        log.exception("article_generation failed")
        try:
            CoreApiClient().job_complete(
                job_id,
                {
                    "status": "failed",
                    "error": str(e)[:1900],
                    "output": {},
                },
            )
        except Exception:
            log.exception("could not notify core-api")
        raise
