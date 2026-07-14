from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class CMSBuilderAgent(BaseAgent):
    name = "cms_builder"
    default_temperature = 0.4

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un éditeur en chef. Tu proposes une structure éditoriale "
            "(catégories, tags, modèle d'article, style d'index blog) adaptée au secteur. "
            "Réponds en JSON strict :\n"
            "{\n"
            '  "categories": [{"slug":"...","name":"..."}],\n'
            '  "tags": [{"slug":"...","name":"..."}],\n'
            '  "article_template": { "outline": ["Intro","Sections...","Conclusion"],\n'
            '                         "word_count": 800, "tone": "professionnel" },\n'
            '  "blog_index_style": "grid|list|magazine"\n'
            "}"
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        return (
            f"Secteur : {brief.get('sector')}. Audience : {brief.get('target_audience')}.\n"
            f"Brief complet :\n{json.dumps(brief, ensure_ascii=False, indent=2)}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict) or "categories" not in parsed:
            raise ValueError("cms_builder: missing 'categories'")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        return {
            "categories": [
                {"slug": "actualites", "name": "Actualités"},
                {"slug": "conseils", "name": "Conseils"},
            ],
            "tags": [{"slug": "general", "name": "Général"}],
            "article_template": {
                "outline": ["Intro", "Développement", "Conclusion"],
                "word_count": 800,
                "tone": "professionnel",
            },
            "blog_index_style": "grid",
        }
