from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class StaticFrontendBuilderAgent(BaseAgent):
    name = "static_frontend_builder"
    default_temperature = 0.55
    default_max_tokens = 16000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es un directeur artistique + senior frontend engineer pour une agence web premium.

Objectif : générer un site statique professionnel, unique, premium, directement déployable.
Tu dois prendre des décisions autonomes : structure, storytelling, design, hiérarchie, sections, micro-interactions, style visuel.

Tu génères UNIQUEMENT du HTML5, CSS3 et JavaScript vanilla.
Interdits : React, Next.js, Vue, Angular, Svelte, Astro, Vite, npm, package.json, backend, imports node_modules.

Qualité attendue :
- Design sur mesure selon le brief, jamais template générique.
- Direction artistique forte et cohérente avec le secteur.
- UX orientée conversion.
- Mobile-first responsive.
- Accessibilité correcte.
- SEO de base : title, description, OpenGraph, JSON-LD.
- Header/footer professionnels.
- CTA spécifiques au business.
- Sections variées et pertinentes.
- CSS complet, structuré, premium, avec variables et composants réutilisables.
- JS léger : menu mobile, smooth scroll, animations sobres, formulaire sans backend avec mailto fallback ou message local.
- Utilise toujours des icônes visuelles professionnelles quand cela améliore la compréhension : SVG inline, pictogrammes CSS, ou icônes vectorielles simples.
- N'utilise jamais d'emoji sauf si le brief utilisateur le demande explicitement.

Catalogue de composants autorisés pour standardiser la génération :
- Layout : Container, Section, Grid, Stack, Spacer, Divider, Header, Navbar, MobileMenu, Breadcrumb, Footer.
- Hero : HeroCentered, HeroSplit, HeroVideo, HeroImage, HeroMinimal, HeroWithForm, HeroSlider.
- Marketing : FeaturesGrid, FeatureCard, ServicesList, ServiceCard, StatsCounter, Timeline, ProcessSteps, MissionVision, WhyChooseUs.
- Social proof : Testimonials, TestimonialsCarousel, ReviewCard, LogoCloud, CaseStudies, TrustedBy.
- Pricing : PricingTable, PricingCard, ComparisonTable, PricingToggle, FeatureComparison.
- Media : Gallery, GalleryGrid, ImageCard, VideoSection, Lightbox, PortfolioGrid.
- Blog/CMS : BlogGrid, BlogList, BlogCard, FeaturedPost, BlogPost, ArticleHeader, ArticleContent, AuthorBox, RelatedPosts, BlogSidebar, BlogCategories, BlogTags, BlogSearch, Pagination.
- Contact : ContactForm, NewsletterForm, QuoteForm, ReservationForm, ContactInfo, MapSection, OpeningHours.
- Support : FAQ, FAQAccordion, HelpCenter, SupportCard.
- E-commerce optionnel : ProductsGrid, ProductCard, ProductDetails, CartDrawer, CheckoutForm, OrderSummary.
- Restaurant/hôtel optionnel : MenuSection, MenuCard, ChefSection, RoomsGrid, BookingCTA.
- CTA : CTABanner, CTASection, CTAInline, DownloadAppCTA.
- UI base : Button, IconButton, Heading, Paragraph, Badge, Card, InfoCard, Input, Textarea, Select, Checkbox.
- Builder : SectionRenderer, ComponentRegistry, ThemeProvider, StyleManager, PageRenderer, DragHandle, DropZone.
- SEO/performance : SEOHead, StructuredData, CookieBanner, ConsentManager, LazyImage.
- Responsive : DesktopOnly, MobileOnly, TabletView, ResponsiveGrid.

MVP obligatoire quand pertinent :
- Header, Footer, Hero, FeaturesGrid, ServicesList, Testimonials, PricingTable, FAQ, Gallery, ContactForm, BlogCard, BlogPost, CTASection.
- Toujours produire une structure HTML avec des classes de composants nommées clairement, par exemple : component-header, component-hero-split, component-features-grid.
- Dans le JSON final, chaque entrée de "sections" doit inclure au minimum : id, component, title, content, enabled.

Tu dois retourner du JSON strict, sans markdown, au format exact :
{
  "files": [
    {"path": "index.html", "content": "<!doctype html>..."},
    {"path": "styles.css", "content": "..."},
    {"path": "script.js", "content": "..."}
  ],
  "design_tokens": {
    "primary": "#...",
    "secondary": "#...",
    "accent": "#...",
    "background": "#...",
    "surface": "#...",
    "text": "#...",
    "font_heading": "...",
    "font_body": "...",
    "ui_style": "..."
  },
  "sections": [
    {"id": "hero", "component": "HeroSplit", "title": "...", "content": "...", "enabled": true}
  ],
  "notes": []
}

Contraintes fichiers :
- index.html doit lier ./styles.css et ./script.js.
- Tous les assets externes doivent être HTTPS.
- Pas de lorem ipsum, pas de TODO, pas de placeholder évident.
- Le site doit fonctionner en ouvrant index.html directement.
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        designer = inp.context.get("designer", {})
        copywriter = inp.context.get("copywriter", {})
        seo = inp.context.get("seo", {})
        strategy = inp.context.get("strategy_director", {})
        ux = inp.context.get("ux_architect", {})
        site_planner = inp.context.get("site_planner", {})
        locale = inp.locale or "fr"

        # Extract SiteBlueprint structured fields
        sections_blueprint = brief.get("sections", [])
        brand = brief.get("brand", {})
        contact = brief.get("contact", {})
        social = brief.get("social", {})
        tone = brand.get("tone") or brief.get("tone", "professionnel")
        style_keywords = brand.get("style_keywords") or brief.get("style_keywords", [])
        font_heading = brand.get("font_heading") or brief.get("font_style") or "Inter"
        font_body = brand.get("font_body") or brief.get("font_style") or "Inter"
        target_audience = brief.get("target_audience") or ""
        objectives = brief.get("objectives") or ""

        parts = [
            f"Langue du site : {locale}\n",
            f"Brief complet :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n",
            f"Design system (utilise EXACTEMENT ces tokens pour les CSS variables — ne pas inventer des couleurs) :\n"
            f"{json.dumps(designer, ensure_ascii=False, indent=2)}\n",
        ]

        if tone or style_keywords:
            parts.append(
                f"Ton et ambiance : {tone}. Mots-clés de style : {', '.join(style_keywords) if style_keywords else 'non spécifiés'}.\n"
                f"Typographies : heading={font_heading}, body={font_body}.\n"
            )

        if target_audience:
            parts.append(f"Audience cible : {target_audience}.\n")
        if objectives:
            parts.append(f"Objectifs du site : {objectives}.\n")

        if contact or social:
            contact_info = {**contact, "social": social}
            parts.append(f"Coordonnées réelles à utiliser dans le footer et la section contact :\n{json.dumps(contact_info, ensure_ascii=False, indent=2)}\n")

        if sections_blueprint:
            enabled = [s for s in sections_blueprint if s.get("enabled", False)]
            if enabled:
                parts.append(
                    f"SECTIONS DEMANDÉES PAR LE CLIENT (ORDRE OBLIGATOIRE — génère EXACTEMENT ces sections dans cet ordre) :\n"
                    f"{json.dumps(enabled, ensure_ascii=False, indent=2)}\n"
                    "IMPORTANT : Pour chaque section, si 'data' contient des valeurs non vides (headline, items, plans, etc.), "
                    "utilise-les telles quelles dans le HTML. Ne pas réécrire, ne pas ignorer, ne pas substituer par un texte générique.\n"
                )

        if copywriter:
            parts.append(f"Contenu copywriter (textes à utiliser directement) :\n{json.dumps(copywriter, ensure_ascii=False, indent=2)}\n")
        if seo:
            parts.append(f"SEO :\n{json.dumps(seo, ensure_ascii=False, indent=2)}\n")
        if strategy:
            strategy_summary = {
                k: strategy.get(k)
                for k in ("positioning", "usp", "emotional_angle", "tone_of_voice", "target_persona")
                if strategy.get(k)
            }
            if strategy_summary:
                parts.append(f"Stratégie de marque :\n{json.dumps(strategy_summary, ensure_ascii=False, indent=2)}\n")
        if ux:
            ux_summary = {k: ux.get(k) for k in ("conversion_points", "cta_hierarchy", "trust_signals") if ux.get(k)}
            if ux_summary:
                parts.append(f"Architecture UX :\n{json.dumps(ux_summary, ensure_ascii=False, indent=2)}\n")
        if site_planner:
            parts.append(f"Plan du site :\n{json.dumps(site_planner, ensure_ascii=False, indent=2)}\n")

        parts.append(
            "Génère maintenant un site statique unique, premium et complet. "
            "Ne fais pas un template générique. Respecte l'ordre des sections demandées. "
            "Utilise les contenus fournis par le client mot pour mot. "
            "IMPORTANT : utilise les CSS custom properties --primary, --secondary, --accent issues du design system fourni ci-dessus."
        )
        return "\n".join(parts)

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise ValueError("static_frontend_builder: expected object")
        files = parsed.get("files")
        if not isinstance(files, list):
            raise ValueError("static_frontend_builder: missing files")
        normalized = _normalize_files(files)
        paths = {f["path"] for f in normalized}
        missing = {"index.html", "styles.css", "script.js"} - paths
        if missing:
            raise ValueError(f"static_frontend_builder: missing files {sorted(missing)}")
        return {
            "files": normalized,
            "generated_files": normalized,
            "design_tokens": parsed.get("design_tokens") if isinstance(parsed.get("design_tokens"), dict) else {},
            "sections": parsed.get("sections") if isinstance(parsed.get("sections"), list) else [],
            "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [],
        }

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        designer = inp.context.get("designer", {})
        business = brief.get("business_name") or brief.get("name") or "Votre marque"
        sector = brief.get("sector") or "services"
        description = brief.get("description") or brief.get("brief") or "Une expérience professionnelle pensée pour convertir."
        # Lire les tokens réels du designer, avec fallback uniquement si absent
        palette = (designer.get("palette") or {}) if isinstance(designer, dict) else {}
        typography = (designer.get("typography") or {}) if isinstance(designer, dict) else {}
        tokens = {
            "primary": palette.get("primary") or "#6366f1",
            "secondary": palette.get("secondary") or "#1e1b4b",
            "accent": palette.get("accent") or "#22d3ee",
            "background": palette.get("bg") or "#f8fafc",
            "surface": palette.get("surface") or "#ffffff",
            "text": palette.get("text") or "#0f172a",
            "font_heading": typography.get("heading") or "Inter",
            "font_body": typography.get("body") or "Inter",
            "ui_style": (designer.get("vibe") or "premium modern"),
        }
        html = f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{business} — {sector}</title>
  <meta name=\"description\" content=\"{description}\">
  <meta property=\"og:title\" content=\"{business}\">
  <meta property=\"og:description\" content=\"{description}\">
  <link rel=\"stylesheet\" href=\"./styles.css\">
</head>
<body>
  <header class=\"site-header\"><a class=\"brand\" href=\"#hero\">{business}</a><nav><a href=\"#services\">Services</a><a href=\"#about\">À propos</a><a href=\"#contact\">Contact</a></nav></header>
  <main>
    <section id=\"hero\" class=\"hero\"><p class=\"eyebrow\">{sector}</p><h1>{business}, une présence web pensée pour inspirer confiance.</h1><p>{description}</p><a class=\"button\" href=\"#contact\">Parler du projet</a></section>
    <section id=\"services\" class=\"grid\"><article><h2>Stratégie claire</h2><p>Un message lisible et orienté conversion.</p></article><article><h2>Expérience premium</h2><p>Une interface élégante et rapide.</p></article><article><h2>Accompagnement</h2><p>Un parcours pensé pour vos visiteurs.</p></article></section>
    <section id=\"about\" class=\"split\"><h2>Une approche sur mesure</h2><p>Nous adaptons le contenu, le ton et la structure à votre audience.</p></section>
    <section id=\"contact\" class=\"contact\"><h2>Contact</h2><form><input placeholder=\"Nom\"><input placeholder=\"Email\"><textarea placeholder=\"Message\"></textarea><button>Envoyer</button></form></section>
  </main>
  <footer>© {business}</footer>
  <script src=\"./script.js\" defer></script>
</body>
</html>"""
        css = """:root{--primary:#2563eb;--secondary:#0f172a;--accent:#f59e0b;--bg:#f8fafc;--surface:#fff;--text:#0f172a}*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--text)}.site-header{position:sticky;top:0;display:flex;justify-content:space-between;align-items:center;padding:20px 7vw;background:rgba(255,255,255,.82);backdrop-filter:blur(16px);border-bottom:1px solid #e2e8f0}.brand{font-weight:800;color:var(--secondary);text-decoration:none}nav{display:flex;gap:22px}nav a{color:#475569;text-decoration:none}.hero{padding:120px 7vw 90px;background:radial-gradient(circle at top right,#dbeafe,transparent 34%),linear-gradient(135deg,#fff,#eff6ff)}.eyebrow{color:var(--primary);font-weight:800;text-transform:uppercase;letter-spacing:.14em}h1{max-width:900px;font-size:clamp(42px,7vw,82px);line-height:.95;margin:16px 0}h2{font-size:clamp(28px,4vw,48px)}p{font-size:18px;line-height:1.7;color:#475569}.button,button{display:inline-flex;border:0;border-radius:999px;background:var(--secondary);color:#fff;padding:15px 24px;text-decoration:none;font-weight:800}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:80px 7vw}.grid article,.split,.contact{background:var(--surface);border:1px solid #e2e8f0;border-radius:28px;padding:34px;box-shadow:0 24px 60px rgba(15,23,42,.08)}.split,.contact{margin:0 7vw 40px}.contact form{display:grid;gap:14px;max-width:620px}input,textarea{width:100%;padding:14px 16px;border:1px solid #cbd5e1;border-radius:16px;font:inherit}textarea{min-height:130px}footer{text-align:center;padding:40px;color:#64748b}@media(max-width:780px){nav{display:none}.grid{grid-template-columns:1fr}.hero{padding-top:80px}}"""
        js = "document.querySelectorAll('a[href^=\"#\"]').forEach(a=>a.addEventListener('click',e=>{const t=document.querySelector(a.getAttribute('href'));if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth'});}}));document.querySelector('form')?.addEventListener('submit',e=>{e.preventDefault();alert('Merci, votre message a été préparé.');});"
        files = [
            {"path": "index.html", "content": html},
            {"path": "styles.css", "content": css},
            {"path": "script.js", "content": js},
        ]
        return {
            "files": files,
            "generated_files": files,
            "design_tokens": tokens,
            "sections": [],
            "notes": [error],
        }


def _normalize_files(files: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in files:
        if isinstance(item, dict):
            path = str(item.get("path") or "").strip().lstrip("/")
            content = item.get("content")
        else:
            continue
        if not path or ".." in path.split("/"):
            continue
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        normalized.append({"path": path, "content": content})
    return normalized
