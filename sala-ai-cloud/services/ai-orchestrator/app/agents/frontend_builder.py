from __future__ import annotations

import json
import uuid
from typing import Any

from app.agents.base import AgentInput, BaseAgent


ALLOWED_SECTIONS = {
    "hero.split",
    "hero.center",
    "features.grid",
    "about.split",
    "testimonials.carousel",
    "pricing.table",
    "faq.accordion",
    "cta.banner",
    "form.contact",
    "blog.index",
    "richtext",
    "gallery.grid",
}


class FrontendBuilderAgent(BaseAgent):
    name = "frontend_builder"
    default_temperature = 0.45
    default_max_tokens = 9000

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Senior Frontend Architect spécialisé dans les sites premium générés par composants. "
            "Tu ne génères PAS de code HTML/CSS/JS. Tu génères un PageSchema JSON strict pour un renderer Next.js/Tailwind. "
            "Ton objectif est de transformer le brief, le design system, la copy et le SEO en layout très personnalisé, "
            "avec une vraie direction artistique, une hiérarchie UX forte et des props riches pour chaque section.\n\n"
            "Composants autorisés uniquement :\n"
            "- hero.split ou hero.center : props { title, subtitle, cta_primary, cta_secondary, image? }\n"
            "- features.grid : props { title, subtitle?, columns: 2|3|4, items:[{title, desc, icon?}] }\n"
            "- about.split : props { title, body, image? }\n"
            "- testimonials.carousel : props { title?, items:[{author, role?, quote, avatar?}] }\n"
            "- pricing.table : props { title?, plans:[{name, price, period?, features, cta, highlighted?}] }\n"
            "- faq.accordion : props { title?, items:[{q,a}] }\n"
            "- cta.banner : props { title, subtitle?, cta }\n"
            "- form.contact : props { title?, subtitle?, form_id, layout:'single'|'split' }\n"
            "- blog.index : props { title?, style:'grid'|'list'|'magazine', per_page }\n"
            "- richtext : props { markdown }\n"
            "- gallery.grid : props { title?, items:[{url?, alt?}] }\n\n"
            "Qualité attendue :\n"
            "- Le site doit sembler conçu sur mesure pour le secteur et la marque, jamais générique.\n"
            "- Utilise des sections différentes selon les pages, pas une répétition hero/contact partout.\n"
            "- Varie hero.split / hero.center selon l’intention de la page.\n"
            "- Ajoute richtext quand une page a besoin d’un contenu éditorial structuré.\n"
            "- Utilise les couleurs, le ton, la typographie et l’objectif business du brief.\n"
            "- Chaque CTA doit avoir un libellé spécifique, pas seulement 'Contact'.\n"
            "- Chaque page doit avoir 3 à 7 sections pertinentes.\n"
            "- Si stack == onepage : exactement une page slug 'home' avec toutes les sections.\n"
            "- Si stack == multipage : respecte les pages demandées et personnalise chaque page.\n"
            "- Les ids de section doivent être stables, courts et lisibles.\n\n"
            "Réponds STRICTEMENT en JSON valide, sans markdown, au format :\n"
            "{\n"
            "  \"page_schema\": {\n"
            "    \"pages\": [\n"
            "      {\n"
            "        \"meta\": { \"slug\": \"home\", \"title\": \"...\", \"description\": \"...\", \"og\": {}, \"schema_org\": {} },\n"
            "        \"layout\": { \"header_id\": \"default\", \"footer_id\": \"default\" },\n"
            "        \"sections\": [\n"
            "          { \"id\": \"hero-home\", \"type\": \"hero.split\", \"props\": { \"title\": \"...\", \"subtitle\": \"...\" } }\n"
            "        ]\n"
            "      }\n"
            "    ]\n"
            "  },\n"
            "  \"components_used\": []\n"
            "}"
        )

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        designer = inp.context.get("designer", {})
        copywriter = inp.context.get("copywriter", {})
        seo = inp.context.get("seo", {})
        form = inp.context.get("form_builder", {})
        cms = inp.context.get("cms_builder", {})
        return (
            "Construis un PageSchema premium et personnalisé à partir de ces données.\n\n"
            f"Brief onboarding :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            f"Design tokens / direction artistique :\n{json.dumps(designer, ensure_ascii=False, indent=2)}\n\n"
            f"Copywriter output :\n{json.dumps(copywriter, ensure_ascii=False, indent=2)}\n\n"
            f"SEO output :\n{json.dumps(seo, ensure_ascii=False, indent=2)}\n\n"
            f"Form output :\n{json.dumps(form, ensure_ascii=False, indent=2)}\n\n"
            f"CMS/blog output :\n{json.dumps(cms, ensure_ascii=False, indent=2)}\n\n"
            "Important : conserve les textes de copywriter quand ils sont bons, mais améliore la structure UX, "
            "la variété des sections et les props du renderer pour obtenir un site moins template."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("frontend_builder: expected object")
        page_schema = parsed.get("page_schema")
        if not isinstance(page_schema, dict):
            raise ValueError("frontend_builder: missing page_schema")
        pages = page_schema.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError("frontend_builder: page_schema.pages empty")

        form = inp.context.get("form_builder", {})
        form_id = form.get("id", "contact-form")
        normalized_pages: list[dict[str, Any]] = []
        components_used: set[str] = set()

        for page_index, page in enumerate(pages):
            if not isinstance(page, dict):
                continue
            meta = page.get("meta") if isinstance(page.get("meta"), dict) else {}
            slug = str(meta.get("slug") or page.get("slug") or ("home" if page_index == 0 else f"page-{page_index}"))
            title = str(meta.get("title") or page.get("title") or slug.title())
            sections_in = page.get("sections") if isinstance(page.get("sections"), list) else []
            sections_out: list[dict[str, Any]] = []

            for section_index, section in enumerate(sections_in):
                if not isinstance(section, dict):
                    continue
                stype = section.get("type")
                if stype not in ALLOWED_SECTIONS:
                    continue
                props = section.get("props") if isinstance(section.get("props"), dict) else {}
                if stype == "form.contact":
                    props = {**props, "form_id": str(props.get("form_id") or form_id)}
                    if props.get("layout") not in {"single", "split"}:
                        props["layout"] = "split"
                if stype == "features.grid" and props.get("columns") not in {2, 3, 4}:
                    props["columns"] = 3
                sid = str(section.get("id") or f"{stype.replace('.', '-')}-{slug}-{section_index}")
                sections_out.append({"id": sid, "type": stype, "props": props})
                components_used.add(stype)

            if not sections_out:
                sections_out = self._fallback_sections(slug, title, inp)
                components_used.update(s["type"] for s in sections_out)

            normalized_pages.append(
                {
                    "meta": {
                        "slug": slug,
                        "title": title,
                        "description": str(meta.get("description") or ""),
                        "og": meta.get("og") if isinstance(meta.get("og"), dict) else {},
                        "schema_org": meta.get("schema_org") if isinstance(meta.get("schema_org"), dict) else {},
                    },
                    "layout": {"header_id": "default", "footer_id": "default"},
                    "sections": sections_out,
                }
            )

        stack = inp.context.get("brief", {}).get("stack")
        if stack == "onepage":
            normalized_pages = [next((p for p in normalized_pages if p["meta"]["slug"] == "home"), normalized_pages[0])]
            normalized_pages[0]["meta"]["slug"] = "home"

        return {
            "page_schema": {"pages": normalized_pages},
            "components_used": sorted(components_used),
        }

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        copy = inp.context.get("copywriter", {})
        pages = copy.get("pages") if isinstance(copy.get("pages"), list) else []
        normalized_pages = []
        for page in pages:
            slug = page.get("slug", "home") if isinstance(page, dict) else "home"
            title = page.get("title", slug.title()) if isinstance(page, dict) else slug.title()
            normalized_pages.append(
                {
                    "meta": {"slug": slug, "title": title, "description": "", "og": {}, "schema_org": {}},
                    "layout": {"header_id": "default", "footer_id": "default"},
                    "sections": self._fallback_sections(slug, title, inp),
                }
            )
        if not normalized_pages:
            normalized_pages = [
                {
                    "meta": {"slug": "home", "title": "Accueil", "description": "", "og": {}, "schema_org": {}},
                    "layout": {"header_id": "default", "footer_id": "default"},
                    "sections": self._fallback_sections("home", "Accueil", inp),
                }
            ]
        return {"page_schema": {"pages": normalized_pages}, "components_used": sorted(ALLOWED_SECTIONS)}

    def _fallback_sections(self, slug: str, title: str, inp: AgentInput) -> list[dict[str, Any]]:
        brief = inp.context.get("brief", {})
        name = brief.get("business_name") or brief.get("name") or "Votre marque"
        tagline = brief.get("tagline") or brief.get("description") or "Un site professionnel pensé pour convertir."
        sector = brief.get("sector") or "votre secteur"
        form = inp.context.get("form_builder", {})
        form_id = form.get("id", "contact-form")
        uid = lambda label: f"{label}-{slug}-{uuid.uuid4().hex[:6]}"
        
        hero_title = title if slug != "home" else f"{name}, l'excellence en {sector}"
        hero_subtitle = tagline
        
        return [
            {
                "id": uid("hero"),
                "type": "hero.center",
                "props": {
                    "title": hero_title,
                    "subtitle": hero_subtitle,
                    "cta_primary": {"label": "Démarrer", "href": "#contact"},
                    "cta_secondary": {"label": "En savoir plus", "href": "#features"},
                },
            },
            {
                "id": uid("features"),
                "type": "features.grid",
                "props": {
                    "title": f"Pourquoi choisir {name}",
                    "subtitle": f"Nos forces dans le secteur {sector}",
                    "columns": 3,
                    "items": [
                        {"title": "Expertise", "desc": f"Spécialistes en {sector}", "icon": "star"},
                        {"title": "Qualité", "desc": "Résultats garantis et mesurables", "icon": "check"},
                        {"title": "Support", "desc": "Accompagnement personnalisé", "icon": "heart"},
                    ],
                },
            },
            {
                "id": uid("contact"),
                "type": "form.contact",
                "props": {"title": f"Parlons de votre projet", "subtitle": "Réponse rapide et personnalisée.", "form_id": form_id, "layout": "split"},
            },
        ]
