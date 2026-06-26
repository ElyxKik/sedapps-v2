from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class UXArchitectAgent(BaseAgent):
    name = "ux_architect"
    default_temperature = 0.35
    default_max_tokens = 6000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es UX Architect senior pour sites premium 10K+.

Tu dois renforcer le parcours utilisateur, les intentions de pages, la conversion, la profondeur des sections et la cohérence multi-page.

Retourne uniquement du JSON strict :
{
  "ux_principles": ["..."],
  "page_flow": [
    {"page_path": "index.html", "goal": "...", "key_sections": ["..."]}
  ],
  "conversion_points": ["..."],
  "friction_reducers": ["..."],
  "premium_components": ["..."]
}
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        return (
            f"Brief :\n{json.dumps(inp.context.get('brief', {}), ensure_ascii=False, indent=2)}\n\n"
            f"Stratégie :\n{json.dumps(inp.context.get('strategy_director', {}), ensure_ascii=False, indent=2)}\n\n"
            f"Plan :\n{json.dumps(inp.context.get('site_planner', {}), ensure_ascii=False, indent=2)}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("ux_architect: expected object")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        pages = inp.context.get("site_planner", {}).get("pages", [])
        return {
            "ux_principles": ["Hiérarchie claire", "CTA contextuels", "Preuves visibles", "Navigation simple"],
            "page_flow": [
                {"page_path": page.get("path", "index.html"), "goal": page.get("purpose", "Convertir"), "key_sections": page.get("components", [])}
                for page in pages
                if isinstance(page, dict)
            ],
            "conversion_points": ["Hero CTA", "CTA après preuves", "Contact final"],
            "friction_reducers": ["FAQ", "Process clair", "Preuves de confiance"],
            "premium_components": ["CaseStudies", "Testimonials", "ProcessSteps", "FAQ", "CTASection"],
            "notes": [error],
        }
