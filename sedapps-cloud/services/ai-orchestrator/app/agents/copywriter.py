from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class CopywriterAgent(BaseAgent):
    name = "copywriter"
    default_temperature = 0.7
    default_max_tokens = 6000

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Copywriter senior, expert en conversion et SEO. "
            "Tu rédiges des textes marketing dans la langue demandée, "
            "avec un ton adapté au brief. Pas de bullshit corporate. "
            "Réponds STRICTEMENT en JSON valide (objet unique).\n"
            "Schéma :\n"
            "{\n"
            '  "pages": [\n'
            "    {\n"
            '      "slug": "home",\n'
            '      "title": "string",\n'
            '      "sections": [\n'
            '        { "type": "hero",       "title":"...", "subtitle":"...", "cta_primary":"...", "cta_secondary":"..." },\n'
            '        { "type": "features",   "title":"...", "items":[{"title":"...","desc":"...","icon":"..."}] },\n'
            '        { "type": "about",      "title":"...", "body":"..." },\n'
            '        { "type": "testimonials","items":[{"author":"...","role":"...","quote":"..."}] },\n'
            '        { "type": "pricing",    "plans":[{"name":"...","price":"...","features":["..."],"cta":"..."}] },\n'
            '        { "type": "faq",        "items":[{"q":"...","a":"..."}] },\n'
            '        { "type": "cta_banner", "title":"...", "subtitle":"...", "cta":"..." },\n'
            '        { "type": "contact",    "title":"...", "subtitle":"..." }\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Sélectionne SEULEMENT les sections pertinentes pour chaque page (3-6 par page)."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        design = inp.context.get("designer", {})
        return (
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            f"Design tokens (pour info, ne pas générer de code) :\n"
            f"{json.dumps(design.get('vibe', 'moderne'))}\n\n"
            f"Locale : {inp.locale}. Tonalité : {brief.get('tone', 'professional')}.\n"
            f"Pages demandées : {brief.get('pages', ['home','about','services','contact'])}"
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict) or "pages" not in parsed:
            raise ValueError("copywriter: missing 'pages'")
        pages = parsed["pages"]
        if not isinstance(pages, list) or not pages:
            raise ValueError("copywriter: 'pages' empty")
        return parsed

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        name = brief.get("business_name", "Votre Marque")
        return {
            "pages": [
                {
                    "slug": "home",
                    "title": name,
                    "sections": [
                        {"type": "hero", "title": f"Bienvenue chez {name}",
                         "subtitle": brief.get("tagline") or "Votre nouveau site web professionnel.",
                         "cta_primary": "Nous contacter", "cta_secondary": "En savoir plus"},
                        {"type": "contact", "title": "Contactez-nous",
                         "subtitle": "Nous répondons sous 24h."},
                    ],
                }
            ]
        }
