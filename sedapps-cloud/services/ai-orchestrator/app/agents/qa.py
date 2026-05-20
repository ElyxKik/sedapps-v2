from __future__ import annotations

import json
import time
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage


class QAAgent(BaseAgent):
    """
    Audite le PageSchema final + SEO + formulaire.
    Heuristiques déterministes (rapide, fiable) — un appel LLM facultatif peut être
    branché en V1 pour des recommandations qualitatives.
    """
    name = "qa"

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        t0 = time.perf_counter()
        issues: list[dict[str, Any]] = []
        auto_fixes: list[str] = []

        fg = inp.context.get("frontend_generator", {})
        page_schema = (fg.get("page_schema") or {}).get("pages") or []
        seo = fg.get("seo") or {}

        if not page_schema:
            issues.append({"severity": "critical", "code": "no_pages",
                           "msg": "Aucune page générée."})

        for p in page_schema:
            meta = p.get("meta", {})
            slug = meta.get("slug", "?")
            title = meta.get("title", "")
            desc = meta.get("description", "")
            if not title:
                issues.append({"severity": "high", "code": "missing_title",
                               "page": slug, "msg": "Titre manquant"})
            elif len(title) > 60:
                issues.append({"severity": "medium", "code": "title_too_long",
                               "page": slug, "msg": f"Title {len(title)} chars (>60)"})
            if not desc:
                issues.append({"severity": "medium", "code": "missing_meta_desc",
                               "page": slug, "msg": "Meta description manquante"})
            elif len(desc) > 160:
                issues.append({"severity": "low", "code": "meta_too_long",
                               "page": slug, "msg": f"Meta {len(desc)} chars (>160)"})

            section_types = [s.get("type") for s in p.get("sections", [])]
            if slug == "home" and "hero.split" not in section_types and "hero.center" not in section_types:
                issues.append({"severity": "high", "code": "no_hero",
                               "page": slug, "msg": "Pas de hero sur la home"})
            if "form.contact" not in section_types and slug in ("home", "contact"):
                issues.append({"severity": "medium", "code": "no_contact_form",
                               "page": slug, "msg": "Pas de formulaire de contact"})

        if not seo.get("sitemap"):
            issues.append({"severity": "low", "code": "no_sitemap",
                           "msg": "Sitemap absent"})

        # score : 100 - pondération par sévérité
        weights = {"critical": 30, "high": 10, "medium": 4, "low": 1}
        score = max(0, 100 - sum(weights.get(i["severity"], 1) for i in issues))
        status = "ok" if score >= 80 else "partial"

        data = {
            "score": score,
            "issues": sorted(issues, key=lambda i: self.SEVERITY_ORDER.get(i["severity"], 9)),
            "auto_fixes_applied": auto_fixes,
        }
        return AgentOutput(
            agent=self.name, status=status, data=data,
            tokens=TokenUsage(),
            duration_ms=int((time.perf_counter() - t0) * 1000),
            model="deterministic",
        )

    def system_prompt(self, inp: AgentInput) -> str:  # unused
        return ""

    def user_prompt(self, inp: AgentInput) -> str:  # unused
        return json.dumps(inp.context)
