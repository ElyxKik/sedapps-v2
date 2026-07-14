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
            "Règles de structure :\n"
            "- Si le brief spécifie stack == 'onepage' : génère EXACTEMENT une seule page avec slug 'home'. Toutes les sections (hero, features, about, testimonials, pricing, faq, cta_banner, contact) doivent être sur cette unique page.\n"
            "- Si le brief spécifie stack == 'multipage' : génère une page par élément listé dans 'Pages demandées'. Répartis les sections de manière logique et pertinente sur ces différentes pages (3 à 6 sections par page, chaque page ayant ses propres sections spécifiques)."
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        design = inp.context.get("designer", {})
        stack = brief.get("stack", "multipage")

        if stack == "onepage":
            requested_pages = ["home"]
        else:
            requested_pages = brief.get("pages", ["home", "about", "services", "contact"])

        # Extract structured sections from SiteBlueprint if available
        sections_data = brief.get("sections", [])
        brand = brief.get("brand", {})
        tone = brand.get("tone") or brief.get("tone", "professionnel")
        style_keywords = brand.get("style_keywords") or brief.get("style_keywords", [])
        target_audience = brief.get("target_audience") or ""
        objectives = brief.get("objectives") or ""

        sections_instruction = ""
        if sections_data:
            sections_instruction = (
                f"\n\nSections fournies par le client (PRIORITÉ ABSOLUE — utilise ces données telles quelles si remplies, génère seulement si vide) :\n"
                f"{json.dumps(sections_data, ensure_ascii=False, indent=2)}\n"
                "RÈGLE : Si 'data.headline', 'data.title', 'data.items' etc. sont fournis et non vides, utilise-les exactement. "
                "Génère du contenu IA uniquement pour les champs vides ou manquants."
            )

        return (
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            f"Design tokens (pour info) :\n{json.dumps(design.get('vibe', 'moderne'))}\n\n"
            f"Locale : {inp.locale}. Ton : {tone}. Mots-clés de style : {', '.join(style_keywords) if style_keywords else 'non spécifiés'}.\n"
            f"Stack : {stack}. Pages : {requested_pages}.\n"
            + (f"Audience cible : {target_audience}.\n" if target_audience else "")
            + (f"Objectifs : {objectives}.\n" if objectives else "")
            + sections_instruction
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
        stack = brief.get("stack", "multipage")

        if stack == "onepage":
            pages_list = ["home"]
        else:
            pages_list = brief.get("pages", ["home", "about", "services", "contact"])
            if "home" not in pages_list:
                pages_list = ["home"] + pages_list

        fallback_pages = []
        for p in pages_list:
            if p == "home":
                sections = [
                    {
                        "type": "hero",
                        "title": f"Bienvenue chez {name}",
                        "subtitle": brief.get("tagline") or "Votre nouveau site web professionnel.",
                        "cta_primary": "Nous contacter",
                        "cta_secondary": "En savoir plus",
                    },
                ]
                if stack == "onepage":
                    sections.extend(
                        [
                            {
                                "type": "features",
                                "title": "Nos services",
                                "items": [
                                    {
                                        "title": "Qualité",
                                        "desc": "Prestations de haute qualité.",
                                        "icon": "star",
                                    }
                                ],
                            },
                            {
                                "type": "about",
                                "title": "À propos",
                                "body": f"Découvrez {name}, votre partenaire de confiance.",
                            },
                            {
                                "type": "contact",
                                "title": "Contactez-nous",
                                "subtitle": "Nous répondons sous 24h.",
                            },
                        ]
                    )
                else:
                    sections.append(
                        {
                            "type": "contact",
                            "title": "Contactez-nous",
                            "subtitle": "Nous répondons sous 24h.",
                        }
                    )

                fallback_pages.append({"slug": "home", "title": name, "sections": sections})
            else:
                fallback_pages.append(
                    {
                        "slug": p,
                        "title": f"{name} - {p.capitalize()}",
                        "sections": [
                            {
                                "type": "hero",
                                "title": f"{p.capitalize()}",
                                "subtitle": f"Découvrez notre page {p}.",
                                "cta_primary": "Nous contacter",
                                "cta_secondary": "",
                            },
                            {
                                "type": "contact",
                                "title": "Contact",
                                "subtitle": "Contactez-nous pour toute question.",
                            },
                        ],
                    }
                )
        return {"pages": fallback_pages}
