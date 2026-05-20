from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class SEOAgent(BaseAgent):
    name = "seo"
    default_temperature = 0.3

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Senior SEO Specialist. À partir d'un brief de marque et "
            "d'une liste de pages, produis le SEO on-page pour chaque page : "
            "meta title (<=60), meta description (<=160), keywords (5-10), "
            "Open Graph, schema.org. Réponds en JSON STRICT.\n"
            "{\n"
            '  "per_page": [\n'
            "    {\n"
            '      "slug":"home",\n'
            '      "title":"...",\n'
            '      "meta_description":"...",\n'
            '      "keywords":["..."],\n'
            '      "og":{"title":"...","description":"...","image":""},\n'
            '      "schema_org":{ "@context":"https://schema.org","@type":"Organization","name":"..." }\n'
            "    }\n"
            "  ],\n"
            '  "sitemap": { "include": ["home","about","..."] },\n'
            '  "robots": "User-agent: *\\nAllow: /"\n'
            "}"
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        pages = brief.get("pages") or ["home"]
        return (
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n"
            f"Pages : {pages}\nLocale : {inp.locale}."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict) or "per_page" not in parsed:
            raise ValueError("seo: missing 'per_page'")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        name = brief.get("business_name", "Site")
        pages = brief.get("pages") or ["home"]
        return {
            "per_page": [
                {
                    "slug": p,
                    "title": f"{name} — {p.title()}",
                    "meta_description": brief.get("description") or f"{name}. {p.title()}.",
                    "keywords": [name, p, brief.get("sector", "")],
                    "og": {"title": f"{name} — {p.title()}",
                           "description": brief.get("tagline") or "", "image": ""},
                    "schema_org": {"@context": "https://schema.org",
                                    "@type": "Organization", "name": name},
                }
                for p in pages
            ],
            "sitemap": {"include": pages},
            "robots": "User-agent: *\nAllow: /",
        }
