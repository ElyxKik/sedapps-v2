from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class PremiumQAAgent(BaseAgent):
    name = "premium_qa"
    default_temperature = 0.2
    default_max_tokens = 5000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es QA Director pour livrables agence premium 10K+.

Évalue sévèrement le site généré. Le score doit refléter s'il est vendable comme site premium.

Critères : design, UX, copywriting, cohérence multi-page, SEO, performance, accessibilité, icônes, animations, anti-template, conversion.

Retourne uniquement du JSON strict :
{
  "score": 0,
  "passed": false,
  "strengths": ["..."],
  "issues": ["..."],
  "required_refinements": ["..."],
  "anti_template_score": 0,
  "premium_feel_score": 0,
  "conversion_score": 0,
  "technical_score": 0
}
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        site = inp.context.get("static_site", {})
        compact_files = []
        for item in site.get("generated_files", []):
            if isinstance(item, dict):
                path = str(item.get("path", ""))
                content = str(item.get("content", ""))
                # Provide up to 6000 chars per page — enough for full structure review
                # without exceeding LLM context limits on multipage premium sites
                if len(content) > 6000:
                    # Include head + first 3000 chars + last 3000 chars (catches footer/CTA)
                    compact_files.append({
                        "path": path,
                        "content_head": content[:3000],
                        "content_tail": content[-3000:],
                        "total_chars": len(content),
                    })
                else:
                    compact_files.append({"path": path, "content": content})
        return (
            f"Brief :\n{json.dumps(inp.context.get('brief', {}), ensure_ascii=False, indent=2)}\n\n"
            f"Strategy :\n{json.dumps(inp.context.get('strategy_director', {}), ensure_ascii=False, indent=2)}\n\n"
            f"Site files ({len(compact_files)} pages) :\n{json.dumps(compact_files, ensure_ascii=False, indent=2)}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("premium_qa: expected object")
        score = parsed.get("score")
        try:
            score_int = int(score)
        except (TypeError, ValueError):
            score_int = 0
        score_int = max(0, min(100, score_int))
        parsed["score"] = score_int
        parsed["passed"] = bool(parsed.get("passed")) and score_int >= 85
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        return {
            "score": 72,
            "passed": False,
            "strengths": ["Site statique généré", "Structure multi-page disponible"],
            "issues": ["QA premium fallback utilisée", error],
            "required_refinements": ["Renforcer différenciation", "Ajouter preuves", "Améliorer détails premium"],
            "anti_template_score": 70,
            "premium_feel_score": 70,
            "conversion_score": 72,
            "technical_score": 78,
        }
