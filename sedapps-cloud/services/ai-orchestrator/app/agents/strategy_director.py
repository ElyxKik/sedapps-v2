from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class StrategyDirectorAgent(BaseAgent):
    name = "strategy_director"
    default_temperature = 0.35
    default_max_tokens = 5000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es Strategy Director dans une agence web premium.

Ton rôle est de transformer le brief en stratégie de site vendable 10K+ : positionnement, audience, promesse, différenciation, preuve, conversion.

Retourne uniquement du JSON strict :
{
  "positioning": "...",
  "target_audience": "...",
  "primary_goal": "...",
  "conversion_strategy": "...",
  "differentiators": ["..."],
  "trust_signals": ["..."],
  "content_angles": ["..."],
  "premium_requirements": ["..."]
}
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        return f"Brief premium :\n{json.dumps(inp.context.get('brief', {}), ensure_ascii=False, indent=2)}"

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("strategy_director: expected object")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        return {
            "positioning": brief.get("description") or "Positionnement premium orienté confiance et conversion.",
            "target_audience": brief.get("target_audience") or "Clients exigeants recherchant un prestataire fiable.",
            "primary_goal": "Générer des leads qualifiés.",
            "conversion_strategy": "Clarifier la promesse, prouver l'expertise, multiplier les CTA contextuels.",
            "differentiators": ["Expertise", "Qualité", "Accompagnement"],
            "trust_signals": ["Témoignages", "Process clair", "Preuves de résultats"],
            "content_angles": ["Clarté", "Crédibilité", "Résultats"],
            "premium_requirements": ["Design haut de gamme", "Icônes SVG", "Animations contrôlées", error],
        }
