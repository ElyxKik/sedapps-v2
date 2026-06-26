from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class SitePlannerAgent(BaseAgent):
    name = "site_planner"
    default_temperature = 0.35
    default_max_tokens = 5000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es un Site Director senior. Ton rôle est de planifier un site multi-page premium avant toute génération HTML.

Tu dois décider :
- Les pages nécessaires selon le brief.
- Le slug/fichier de chaque page.
- Les sections et composants à utiliser sur chaque page.
- Le storytelling global.
- Les CTA principaux.

Le site ne doit pas être une landing page unique sauf si le brief le demande explicitement.
Par défaut, crée 3 à 6 pages pertinentes.
Si brief.stack == "onepage", crée une seule page index.html riche en sections.
Si brief.stack == "multipage", crée plusieurs pages HTML reliées par navigation.
Si brief.premium == true :
- Crée un site plus riche, plus éditorial et plus haut de gamme.
- Privilégie 5 à 7 pages quand le stack est multipage.
- Ajoute davantage de preuves, storytelling, sections de confiance, cas clients, FAQ et CTA.
- Chaque page doit avoir une intention forte et une composition premium.

Catalogue MVP prioritaire : Header, Footer, Hero, FeaturesGrid, ServicesList, Testimonials, PricingTable, FAQ, Gallery, ContactForm, BlogCard, BlogPost, CTASection.
Les pages doivent utiliser des icônes professionnelles quand utile, mais aucun emoji sauf demande explicite de l'utilisateur.

Retourne uniquement du JSON strict :
{
  "site_goal": "...",
  "navigation": [
    {"label": "Accueil", "href": "index.html"}
  ],
  "pages": [
    {
      "id": "home",
      "title": "...",
      "slug": "index",
      "path": "index.html",
      "purpose": "...",
      "seo_description": "...",
      "components": ["Header", "HeroSplit", "FeaturesGrid", "CTASection", "Footer"],
      "sections": [
        {"id": "hero", "component": "HeroSplit", "title": "...", "intent": "..."}
      ]
    }
  ],
  "design_direction": {
    "style": "...",
    "mood": "...",
    "layout_principles": ["..."]
  }
}
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        stack = str(brief.get("stack") or "").strip().lower() or "multipage"
        if stack in {"monopage", "onepage", "one-page", "singlepage", "single-page"}:
            stack = "onepage"
        premium = bool(brief.get("premium"))
        constraint = (
            "Stack imposé : ONEPAGE. Tu DOIS retourner exactement 1 page (path=index.html) très riche en sections."
            if stack == "onepage"
            else f"Stack imposé : MULTIPAGE. Tu DOIS retourner {'5 à 7' if premium else '3 à 5'} pages reliées par navigation."
        )
        return (
            f"Langue : {inp.locale}\n\n"
            f"{constraint}\n\n"
            "Brief :\n"
            f"{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
            "Planifie le site selon le stack imposé. Ne génère pas de HTML."
        )

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("site_planner: expected object")
        brief = inp.context.get("brief", {})
        stack = str(brief.get("stack") or "").strip().lower()
        if stack in {"monopage", "onepage", "one-page", "singlepage", "single-page"}:
            stack = "onepage"
        pages = parsed.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError("site_planner: missing pages")
        normalized_pages = []
        seen_paths: set[str] = set()
        for index, page in enumerate(pages):
            if not isinstance(page, dict):
                continue
            title = str(page.get("title") or page.get("id") or f"Page {index + 1}").strip()
            raw_slug = str(page.get("slug") or page.get("id") or title).strip().lower()
            slug = _slugify(raw_slug) or f"page-{index + 1}"
            path = "index.html" if index == 0 or slug in {"home", "accueil", "index"} else f"{slug}.html"
            path = str(page.get("path") or path).strip().lstrip("/")
            if not path.endswith(".html"):
                path = f"{path}.html"
            if path in seen_paths:
                continue
            seen_paths.add(path)
            raw_sections = page.get("sections") if isinstance(page.get("sections"), list) else []
            if not raw_sections:
                raw_sections = _default_sections_for_page(slug, index)
            normalized_pages.append({
                "id": str(page.get("id") or slug),
                "title": title,
                "slug": slug,
                "path": path,
                "purpose": str(page.get("purpose") or ""),
                "seo_description": str(page.get("seo_description") or ""),
                "components": page.get("components") if isinstance(page.get("components"), list) else [],
                "sections": raw_sections,
            })
        if not any(page["path"] == "index.html" for page in normalized_pages):
            normalized_pages[0]["path"] = "index.html"

        # Force user's stack choice (onepage / multipage)
        if stack == "onepage":
            first = normalized_pages[0]
            first["path"] = "index.html"
            first["slug"] = "index"
            normalized_pages = [first]
        elif stack == "multipage" and len(normalized_pages) < 2:
            premium = bool(brief.get("premium"))
            extras = [
                {"id": "services", "title": "Services", "slug": "services", "path": "services.html",
                 "purpose": "Détailler l'offre", "seo_description": "",
                 "components": ["Header", "ServicesList", "ProcessSteps", "FAQ", "Footer"], "sections": []},
                {"id": "about", "title": "À propos", "slug": "about", "path": "about.html",
                 "purpose": "Créer la confiance", "seo_description": "",
                 "components": ["Header", "MissionVision", "Testimonials", "Footer"], "sections": []},
                {"id": "contact", "title": "Contact", "slug": "contact", "path": "contact.html",
                 "purpose": "Convertir", "seo_description": "",
                 "components": ["Header", "ContactForm", "ContactInfo", "Footer"], "sections": []},
            ]
            if premium:
                extras.insert(2, {"id": "case-studies", "title": "Cas clients", "slug": "case-studies",
                                  "path": "case-studies.html", "purpose": "Prouver les résultats",
                                  "seo_description": "",
                                  "components": ["Header", "CaseStudies", "Testimonials", "CTASection", "Footer"],
                                  "sections": []})
            existing_paths = {p["path"] for p in normalized_pages}
            for extra in extras:
                if extra["path"] not in existing_paths:
                    normalized_pages.append(extra)
                    existing_paths.add(extra["path"])

        return {
            "site_goal": parsed.get("site_goal") or "site vitrine premium",
            "navigation": parsed.get("navigation") if isinstance(parsed.get("navigation"), list) else [],
            "pages": normalized_pages[:8],
            "design_direction": parsed.get("design_direction") if isinstance(parsed.get("design_direction"), dict) else {},
        }

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        business = brief.get("business_name") or brief.get("name") or "Accueil"
        stack = str(brief.get("stack") or "").strip().lower()
        if stack in {"monopage", "onepage", "one-page", "singlepage", "single-page"}:
            stack = "onepage"
        tagline = brief.get("tagline") or brief.get("description") or "Un site professionnel pensé pour convertir."
        sector = brief.get("sector") or "votre secteur"
        
        if stack == "onepage":
            return {
                "site_goal": brief.get("description") or brief.get("brief") or f"Site one-page pour {business}",
                "navigation": [{"label": "Accueil", "href": "index.html"}],
                "pages": [
                    {"id": "home", "title": business, "slug": "index", "path": "index.html",
                     "purpose": "Présenter, convaincre et convertir sur une seule page",
                     "seo_description": tagline,
                     "components": ["Header", "HeroSplit", "FeaturesGrid", "Testimonials", "FAQ", "CTASection", "ContactForm", "Footer"],
                     "sections": []}
                ],
                "design_direction": {"style": "premium modern", "mood": "confident",
                                     "layout_principles": ["clear hierarchy", "strong CTAs"]},
                "notes": [error],
            }
        
        pages_from_brief = brief.get("pages", [])
        if isinstance(pages_from_brief, list) and pages_from_brief:
            pages = []
            nav = []
            for idx, page_name in enumerate(pages_from_brief[:6]):
                slug = _slugify(page_name) or f"page-{idx}"
                path = "index.html" if idx == 0 else f"{slug}.html"
                title = page_name.title() if isinstance(page_name, str) else f"Page {idx + 1}"
                pages.append({
                    "id": slug, "title": title, "slug": slug, "path": path,
                    "purpose": f"Page {title.lower()} de {business}",
                    "seo_description": "",
                    "components": ["Header", "HeroSplit", "FeaturesGrid", "Footer"],
                    "sections": []
                })
                nav.append({"label": title, "href": path})
            
            return {
                "site_goal": brief.get("description") or f"Site multipage pour {business}",
                "navigation": nav,
                "pages": pages,
                "design_direction": {"style": "premium modern", "mood": "confident", "layout_principles": ["clear hierarchy", "strong CTAs"]},
                "notes": [error],
            }
        
        return {
            "site_goal": brief.get("description") or f"Site vitrine pour {business}",
            "navigation": [
                {"label": "Accueil", "href": "index.html"},
                {"label": "Services", "href": "services.html"},
                {"label": "À propos", "href": "about.html"},
                {"label": "Contact", "href": "contact.html"},
            ],
            "pages": [
                {"id": "home", "title": business, "slug": "index", "path": "index.html", "purpose": f"Présenter {business}", "seo_description": tagline, "components": ["Header", "HeroSplit", "FeaturesGrid", "CTASection", "Footer"], "sections": []},
                {"id": "services", "title": "Services", "slug": "services", "path": "services.html", "purpose": f"Détailler les services en {sector}", "seo_description": "", "components": ["Header", "ServicesList", "FAQ", "Footer"], "sections": []},
                {"id": "about", "title": "À propos", "slug": "about", "path": "about.html", "purpose": f"Créer la confiance pour {business}", "seo_description": "", "components": ["Header", "Testimonials", "Footer"], "sections": []},
                {"id": "contact", "title": "Contact", "slug": "contact", "path": "contact.html", "purpose": "Convertir les visiteurs", "seo_description": "", "components": ["Header", "ContactForm", "Footer"], "sections": []},
            ],
            "design_direction": {"style": "premium modern", "mood": "confident", "layout_principles": ["clear hierarchy", "strong CTAs"]},
            "notes": [error],
        }


def _slugify(value: str) -> str:
    cleaned = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-")


def _default_sections_for_page(slug: str, index: int) -> list[dict[str, Any]]:
    """Generate default sections for a page when the LLM returned none."""
    if index == 0 or slug in {"home", "index", "accueil"}:
        return [
            {"id": "hero", "component": "HeroSplit", "title": "Hero", "intent": "Accrocher et présenter la valeur"},
            {"id": "stats", "component": "StatsBar", "title": "Chiffres clés", "intent": "Prouver l'expertise"},
            {"id": "features", "component": "FeaturesGrid", "title": "Pourquoi nous choisir", "intent": "Différencier"},
            {"id": "process", "component": "ProcessSteps", "title": "Notre méthode", "intent": "Rassurer"},
            {"id": "testimonials", "component": "Testimonials", "title": "Témoignages", "intent": "Preuve sociale"},
            {"id": "faq", "component": "FAQ", "title": "Questions fréquentes", "intent": "Levier de conversion"},
            {"id": "cta", "component": "CTASection", "title": "Call to action", "intent": "Convertir"},
            {"id": "contact", "component": "ContactForm", "title": "Contact", "intent": "Convertir"},
        ]
    if slug in {"services", "offre", "prestations"}:
        return [
            {"id": "hero", "component": "HeroSplit", "title": "Hero", "intent": "Présenter les services"},
            {"id": "services", "component": "ServicesList", "title": "Nos prestations", "intent": "Détail de l'offre"},
            {"id": "process", "component": "ProcessSteps", "title": "Méthode", "intent": "Rassurer"},
            {"id": "faq", "component": "FAQ", "title": "FAQ", "intent": "Lever les objections"},
            {"id": "cta", "component": "CTASection", "title": "CTA", "intent": "Convertir"},
        ]
    if slug in {"about", "a-propos", "apropos"}:
        return [
            {"id": "hero", "component": "HeroSplit", "title": "Hero", "intent": "Présenter l'entreprise"},
            {"id": "story", "component": "MissionVision", "title": "Notre histoire", "intent": "Créer la connexion"},
            {"id": "values", "component": "FeaturesGrid", "title": "Nos valeurs", "intent": "Rassurer"},
            {"id": "testimonials", "component": "Testimonials", "title": "Témoignages", "intent": "Preuve sociale"},
            {"id": "cta", "component": "CTASection", "title": "CTA", "intent": "Convertir"},
        ]
    if slug in {"contact", "contactez-nous"}:
        return [
            {"id": "hero", "component": "HeroSplit", "title": "Hero", "intent": "Inviter au contact"},
            {"id": "contact", "component": "ContactForm", "title": "Formulaire", "intent": "Capturer le lead"},
            {"id": "info", "component": "ContactInfo", "title": "Coordonnées", "intent": "Faciliter le contact"},
        ]
    return [
        {"id": "hero", "component": "HeroSplit", "title": "Hero", "intent": "Présenter"},
        {"id": "content", "component": "FeaturesGrid", "title": "Contenu", "intent": "Informer"},
        {"id": "cta", "component": "CTASection", "title": "CTA", "intent": "Convertir"},
    ]
