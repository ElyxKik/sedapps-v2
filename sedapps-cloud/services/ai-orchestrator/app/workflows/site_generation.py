"""
Site-generation workflow — DAG of 9 agents.

Execution plan :
  1. designer
  2. (in parallel) copywriter + seo + form_builder + cms_builder
  3. frontend_generator   (consumes 1+2)
  4. analytics_setup      (deterministic)
  5. blog_writer x N      (optional, only if brief.has_blog)
  6. qa                   (final audit)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agents import (
    AGENT_REGISTRY,
    AgentInput,
    AnalyticsSetupAgent,
    BlogWriterAgent,
    CMSBuilderAgent,
    CopywriterAgent,
    DesignerAgent,
    FormBuilderAgent,
    FrontendGeneratorAgent,
    QAAgent,
    SEOAgent,
)
from app.celery_app import celery
from app.core_client import CoreApiClient

log = logging.getLogger(__name__)


async def _run_agent(agent, ctx: dict[str, Any], inp_base: AgentInput, core: CoreApiClient,
                     job_id: str) -> tuple[str, dict[str, Any], dict[str, int]]:
    inp = AgentInput(
        project_id=inp_base.project_id,
        job_id=inp_base.job_id,
        tenant_id=inp_base.tenant_id,
        locale=inp_base.locale,
        context=ctx,
        params=inp_base.params,
    )
    out = await agent.run(inp)
    core.record_run(job_id, {
        "agent_name": out.agent,
        "model": out.model,
        "prompt_version": getattr(agent, "prompt_version", 1),
        "status": out.status,
        "duration_ms": out.duration_ms,
        "tokens_in": out.tokens.prompt,
        "tokens_out": out.tokens.completion,
        "input": {"context_keys": list(ctx.keys())},
        "output": out.data,
        "warnings": out.warnings,
    })
    return out.agent, out.data, {"in": out.tokens.prompt, "out": out.tokens.completion}


async def _orchestrate(job_id: str, project_id: str, tenant_id: str,
                       brief: dict[str, Any], locale: str) -> dict[str, Any]:
    core = CoreApiClient()
    core.job_start(job_id)

    inp_base = AgentInput(
        project_id=project_id, job_id=job_id, tenant_id=tenant_id,
        locale=locale, context={"brief": brief}, params={},
    )
    context: dict[str, Any] = {"brief": brief}
    total_in = total_out = 0

    async def step(agent, current_ctx):
        name, data, toks = await _run_agent(agent, current_ctx, inp_base, core, job_id)
        return name, data, toks

    # 1. Designer
    name, data, t = await step(DesignerAgent(), context)
    total_in += t["in"]; total_out += t["out"]
    context[name] = data

    # 2. Parallel : copywriter, seo, form_builder, cms_builder (last optional)
    parallel_agents = [CopywriterAgent(), SEOAgent(), FormBuilderAgent()]
    if brief.get("has_blog"):
        parallel_agents.append(CMSBuilderAgent())

    results = await asyncio.gather(*[step(a, context) for a in parallel_agents],
                                   return_exceptions=False)
    for name, data, t in results:
        context[name] = data
        total_in += t["in"]; total_out += t["out"]

    # 3. Frontend generator (deterministic, consumes everything above)
    name, data, t = await step(FrontendGeneratorAgent(), context)
    context[name] = data

    # 4. Analytics setup (deterministic)
    name, data, t = await step(AnalyticsSetupAgent(), context)
    context[name] = data

    # 5. Blog writer (3 seed articles, optional)
    if brief.get("has_blog"):
        cms = context.get("cms_builder", {})
        cats = cms.get("categories") or [{"slug": "general", "name": "Général"}]
        topics = [
            {"topic": f"Introduction au secteur {brief.get('sector', '')}",
             "target_keyword": brief.get("sector", ""),
             "category": cats[0]["slug"], "length": 700},
            {"topic": f"3 conseils pour {brief.get('target_audience', 'nos clients')}",
             "target_keyword": "conseils",
             "category": cats[0]["slug"], "length": 800},
            {"topic": f"Pourquoi choisir {brief.get('business_name', 'notre marque')}",
             "target_keyword": brief.get("business_name", ""),
             "category": cats[0]["slug"], "length": 600},
        ]
        seed_articles = []
        for t_ in topics:
            inp = AgentInput(
                project_id=project_id, job_id=job_id, tenant_id=tenant_id,
                locale=locale, context={"brief": brief}, params=t_,
            )
            out = await BlogWriterAgent().run(inp)
            core.record_run(job_id, {
                "agent_name": out.agent, "model": out.model,
                "status": out.status, "duration_ms": out.duration_ms,
                "tokens_in": out.tokens.prompt, "tokens_out": out.tokens.completion,
                "input": t_, "output": out.data, "warnings": out.warnings,
            })
            total_in += out.tokens.prompt; total_out += out.tokens.completion
            if out.status != "failed":
                seed_articles.append(out.data)
        context["blog_writer"] = {"articles": seed_articles}

    # 6. QA
    name, data, t = await step(QAAgent(), context)
    context[name] = data

    # Final job output
    fg = context.get("frontend_generator", {})
    final = {
        "page_schema": fg.get("page_schema", {}),
        "design_tokens": context.get("designer", {}),
        "seo": fg.get("seo", {}),
        "form": context.get("form_builder", {}),
        "analytics": context.get("analytics_setup", {}),
        "cms": context.get("cms_builder", {}),
        "articles": context.get("blog_writer", {}).get("articles", []),
        "qa": context.get("qa", {}),
    }

    qa_score = (context.get("qa") or {}).get("score", 0)
    status = "success" if qa_score >= 80 else "degraded"

    core.job_complete(job_id, {
        "status": status,
        "error": None,
        "output": final,
        "tokens_in": total_in,
        "tokens_out": total_out,
        "cost_cents": 0,
    })
    return final


@celery.task(name="workflows.site_generation", bind=True, max_retries=1)
def run_site_generation(self, job_id: str, project_id: str, tenant_id: str,
                        brief: dict[str, Any], locale: str = "fr") -> dict[str, Any]:
    log.info("site_generation start job=%s project=%s", job_id, project_id)
    try:
        return asyncio.run(_orchestrate(job_id, project_id, tenant_id, brief, locale))
    except Exception as e:  # noqa: BLE001
        log.exception("site_generation failed")
        try:
            CoreApiClient().job_complete(job_id, {
                "status": "failed", "error": str(e)[:1900], "output": {},
            })
        except Exception:
            log.exception("could not notify core-api of failure")
        raise


# Ensure registry is populated
_ = AGENT_REGISTRY
