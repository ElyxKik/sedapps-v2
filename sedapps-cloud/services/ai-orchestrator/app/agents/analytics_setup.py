from __future__ import annotations

import json
import time
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage


class AnalyticsSetupAgent(BaseAgent):
    """
    Deterministic — pas besoin d'un LLM pour configurer le tracker.
    Génère un tracker_id (basé sur le project_id), une liste d'events par défaut
    et des goals déduits du brief (objectives).
    """
    name = "analytics_setup"

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        t0 = time.perf_counter()
        try:
            brief = inp.context.get("brief", {})
            objectives = brief.get("objectives") or []

            goals: list[dict[str, Any]] = []
            if "conversion" in objectives or "leads" in objectives:
                goals.append({"key": "form_submit", "label": "Soumission de formulaire"})
            if "vente" in objectives or "ecommerce" in objectives:
                goals.append({"key": "purchase", "label": "Achat"})
            if not goals:
                goals.append({"key": "form_submit", "label": "Soumission de formulaire"})

            data = {
                "tracker_id": f"sed-{inp.project_id[:8]}",
                "default_events": [
                    {"key": "pageview", "auto": True},
                    {"key": "click_cta", "selector": "[data-event='cta']"},
                    {"key": "click_whatsapp", "selector": "a[href^='https://wa.me']"},
                    {"key": "click_phone", "selector": "a[href^='tel:']"},
                    {"key": "click_email", "selector": "a[href^='mailto:']"},
                    {"key": "form_submit", "selector": "form[data-track]"},
                ],
                "goals": goals,
                "privacy": {"anonymize_ip": True, "respect_dnt": True, "cookieless": True},
            }
            return AgentOutput(
                agent=self.name, status="ok", data=data,
                tokens=TokenUsage(),
                duration_ms=int((time.perf_counter() - t0) * 1000),
                model="deterministic",
            )
        except Exception as e:  # noqa: BLE001
            return AgentOutput(
                agent=self.name, status="failed", data={},
                duration_ms=int((time.perf_counter() - t0) * 1000),
                warnings=[f"failed: {e}"],
            )

    def system_prompt(self, inp: AgentInput) -> str:  # unused
        return ""

    def user_prompt(self, inp: AgentInput) -> str:  # unused
        return json.dumps(inp.context)
