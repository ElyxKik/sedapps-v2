"""Sector-specific fallback HTML templates for StaticPageBuilderAgent.

Each template generates a unique HTML structure tailored to the sector,
using the brand's design tokens (colors, fonts, logo) from the brief.
"""
from __future__ import annotations

from typing import Any


def _svg(name: str) -> str:
    svgs = {
        "bolt": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        "target": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "star": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "users": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "shield": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        "check": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5"><polyline points="20 6 9 17 4 12"/></svg>',
        "phone": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
        "mail": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
        "map": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>',
        "clock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "utensils": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
        "shopping": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
        "code": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
        "camera": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
        "heart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        "scissors": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>',
        "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "briefcase": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        "trending": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    }
    return svgs.get(name, svgs["star"])


_SECTOR_KEYWORDS: dict[str, list[str]] = {
    "restaurant": ["restaurant", "restauration", "cafe", "bistro", "cuisine", "food", "gastronom", "pizzeria", "boulanger", "bar", "brasserie"],
    "ecommerce": ["ecommerce", "e-commerce", "boutique", "shop", "store", "vente", "produit", "marketplace", "retail"],
    "portfolio": ["portfolio", "photographe", "designer", "artiste", "freelance", "creatif", "agence"],
    "realestate": ["immobilier", "real estate", "realestate", "property"],
    "health": ["sante", "santé", "medical", "medecin", "docteur", "clinic", "clinique", "dentiste", "pharmacie"],
    "fitness": ["fitness", "gym", "sport", "coach", "yoga", "pilates", "musculation", "crossfit"],
    "beauty": ["beaute", "beauté", "salon", "coiffure", "barbier", "ongles", "spa", "esthetique", "esthétique", "massage"],
    "legal": ["avocat", "juridique", "legal", "notaire", "huissier"],
    "tech": ["tech", "software", "logiciel", "saas", "digital", "web", "app", "startup", "developpement"],
    "construction": ["construction", "batiment", "bâtiment", "travaux", "macon", "electricien", "plombier", "architecte"],
    "education": ["education", "éducation", "formation", "cours", "ecole", "école", "academie", "professeur"],
    "consulting": ["consulting", "conseil", "audit", "strategy", "strategie", "management"],
    "travel": ["voyage", "travel", "tourisme", "tourism", "hotel", "hôtel", "location", "vacances"],
    "automotive": ["auto", "automobile", "garage", "mecanique", "voiture"],
}


def detect_sector(brief: dict[str, Any]) -> str:
    sector_raw = (brief.get("sector") or "").lower()
    business = (brief.get("business_name") or "").lower()
    description = (brief.get("description") or brief.get("brief") or "").lower()
    combined = f"{sector_raw} {business} {description}"
    for sector_key, keywords in _SECTOR_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return sector_key
    return "default"


def _head(*, title, business, page_seo_desc, locale, primary, secondary, font_heading) -> str:
    return f"""<!doctype html>
<html lang="{locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — {business}</title>
  <meta name="description" content="{page_seo_desc}">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="./styles.css">
  <script src="./script.js" defer></script>
  <link href="https://fonts.googleapis.com/css2?family={font_heading.replace(' ', '+')}:wght@400;600;700;800&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {{
      theme: {{ extend: {{
        colors: {{ brand: '{primary}', 'brand-secondary': '{secondary}' }},
        fontFamily: {{ heading: ['{font_heading}', 'sans-serif'] }}
      }} }}
    }}
  </script>
  <style>
    h1, h2, h3, h4 {{ font-family: '{font_heading}', sans-serif; }}
    body {{ font-family: '{font_heading}', sans-serif; }}
  </style>
</head>"""


def _header(*, brand_html, nav_html) -> str:
    return f"""<body class="bg-gray-50 text-gray-900">
  <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-4 flex justify-between items-center max-w-7xl mx-auto rounded-full mt-4">
    <a href="index.html">{brand_html}</a>
    <nav class="flex gap-6 items-center">{nav_html}</nav>
  </header>
  <main>"""


def _footer(*, business, sector, audience) -> str:
    return f"""  <footer class="border-t border-gray-100 py-8 text-center text-gray-500 text-sm">
    <p>&copy; {business} — Tous droits réservés.</p>
    <p class="mt-2">Expert en {sector} au service de {audience}.</p>
  </footer>
</body>
</html>"""


def _hero(*, label, title, description, primary, primary_tint, cta1_text, cta1_href, cta2_text, cta2_href) -> str:
    return f"""
    <section class="py-20 text-center flex flex-col items-center" style="background: linear-gradient(to bottom, {primary_tint}, white);">
      <span class="text-sm font-bold tracking-wider uppercase px-3 py-1 rounded-full" style="color: {primary}; background: {primary_tint};">{label}</span>
      <h1 class="text-5xl md:text-6xl font-extrabold tracking-tight mt-6 max-w-4xl" style="color: {primary};">{title}</h1>
      <p class="text-lg text-gray-600 mt-6 max-w-2xl leading-relaxed">{description}</p>
      <div class="mt-10 flex gap-4">
        <a class="px-8 py-3 text-white font-semibold rounded-full shadow-lg transition" style="background: {primary};" href="{cta1_href}">{cta1_text}</a>
        <a class="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-full transition" href="{cta2_href}">{cta2_text}</a>
      </div>
    </section>"""


def _cta_final(*, primary, title, description, button_text, button_href) -> str:
    return f"""
    <section class="text-white py-16 text-center" style="background: {primary};">
      <div class="max-w-3xl mx-auto px-6">
        <h2 class="text-3xl font-bold mb-4">{title}</h2>
        <p class="mb-8" style="color: rgba(255,255,255,0.85);">{description}</p>
        <a class="inline-flex items-center px-8 py-3 bg-white font-semibold rounded-full shadow-lg transition" style="color: {primary};" href="{button_href}">{button_text}</a>
      </div>
    </section>"""


def _testimonials_dark(*, primary, business, sector) -> str:
    return f"""
    <section class="bg-gray-900 text-white py-16">
      <div class="max-w-7xl mx-auto px-6">
        <h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Témoignages</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <blockquote class="bg-gray-800 p-8 rounded-2xl"><p class="text-gray-300 italic">"Une expérience exceptionnelle avec {business}. Je recommande vivement."</p><footer class="mt-4 text-sm"><span class="font-bold text-white">Client 1</span></footer></blockquote>
          <blockquote class="bg-gray-800 p-8 rounded-2xl"><p class="text-gray-300 italic">"Professionnalisme et qualité au rendez-vous. Un vrai partenaire de confiance."</p><footer class="mt-4 text-sm"><span class="font-bold text-white">Client 2</span></footer></blockquote>
          <blockquote class="bg-gray-800 p-8 rounded-2xl"><p class="text-gray-300 italic">"Les résultats ont dépassé nos attentes. Une équipe compétente et à l'écoute."</p><footer class="mt-4 text-sm"><span class="font-bold text-white">Client 3</span></footer></blockquote>
        </div>
      </div>
    </section>"""


def _stats_bar(*, primary, stats: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<div class="p-6 bg-white rounded-2xl border border-gray-100"><div class="text-4xl font-extrabold" style="color: {primary};">{num}</div><div class="text-sm text-gray-500 mt-2">{label}</div></div>'
        for num, label in stats
    )
    return f"""
    <section class="max-w-7xl mx-auto px-6 py-16">
      <div class="grid grid-cols-2 md:grid-cols-{len(stats)} gap-8 text-center">{items}</div>
    </section>"""


def _feature_card(*, primary, primary_tint, icon_name, title, description) -> str:
    return f'<article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition"><div class="w-12 h-12 rounded-xl flex items-center justify-center" style="color: {primary}; background: {primary_tint};">{_svg(icon_name)}</div><h3 class="text-xl font-bold mt-6">{title}</h3><p class="text-gray-600 mt-2">{description}</p></article>'


def _faq_section(*, primary, sector, questions: list[tuple[str, str]]) -> str:
    items = "".join(
        f'<details class="bg-white p-6 rounded-xl border border-gray-100"><summary class="font-bold cursor-pointer">{q}</summary><p class="text-gray-600 mt-3">{a}</p></details>'
        for q, a in questions
    )
    return f"""
    <section class="max-w-4xl mx-auto px-6 py-16">
      <h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Questions fréquentes</h2>
      <div class="space-y-4">{items}</div>
    </section>"""


# ── Sector builders ──────────────────────────────────────────────────────────

def _build_restaurant(*, business, title, tagline, sector, audience, locale,
                      primary, secondary, font_heading, brand_html, nav_html,
                      page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Restaurant", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Voir le menu", cta1_href="#menu", cta2_text="Réserver", cta2_href="contact.html") + f"""
    <section id="menu" class="max-w-5xl mx-auto px-6 py-16">
      <h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Notre carte</h2>
      <div class="space-y-8">
        <div class="flex justify-between items-start pb-6 border-b border-gray-100"><div><h3 class="text-xl font-bold">Entrée du chef</h3><p class="text-gray-600 mt-1">Sélection saisonnière préparée avec des produits frais du marché.</p></div><span class="text-xl font-bold" style="color: {primary};">14€</span></div>
        <div class="flex justify-between items-start pb-6 border-b border-gray-100"><div><h3 class="text-xl font-bold">Plat signature</h3><p class="text-gray-600 mt-1">Spécialité maison, mijotée 6 heures selon la tradition.</p></div><span class="text-xl font-bold" style="color: {primary};">26€</span></div>
        <div class="flex justify-between items-start pb-6 border-b border-gray-100"><div><h3 class="text-xl font-bold">Dessert gourmand</h3><p class="text-gray-600 mt-1">Création pâtissière unique, renouvelée chaque semaine.</p></div><span class="text-xl font-bold" style="color: {primary};">12€</span></div>
        <div class="flex justify-between items-start pb-6 border-b border-gray-100"><div><h3 class="text-xl font-bold">Menu dégustation</h3><p class="text-gray-600 mt-1">5 services accompagnés de vins sélectionnés par notre sommelier.</p></div><span class="text-xl font-bold" style="color: {primary};">65€</span></div>
      </div>
    </section>
    <section class="bg-gray-900 text-white py-16"><div class="max-w-7xl mx-auto px-6"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">L'ambiance</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8"><div class="bg-gray-800 rounded-2xl h-64 flex items-center justify-center text-gray-500">Photo 1</div><div class="bg-gray-800 rounded-2xl h-64 flex items-center justify-center text-gray-500">Photo 2</div><div class="bg-gray-800 rounded-2xl h-64 flex items-center justify-center text-gray-500">Photo 3</div></div></div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + _cta_final(
        primary=primary, title="Réservez votre table", description="Contactez-nous pour réserver. Confirmation sous 24h.",
        button_text="Réserver maintenant", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_ecommerce(*, business, title, tagline, sector, audience, locale,
                     primary, secondary, font_heading, brand_html, nav_html,
                     page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    products = ""
    for name, price in [("Produit premium 1", "49€"), ("Produit premium 2", "79€"), ("Produit premium 3", "129€"), ("Produit premium 4", "199€")]:
        products += f'<article class="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-xl transition"><div class="h-56 bg-gray-100 flex items-center justify-center text-gray-400">Image</div><div class="p-6"><h3 class="font-bold text-lg">{name}</h3><p class="text-gray-600 mt-1 text-sm">Description courte du produit.</p><div class="mt-4 flex justify-between items-center"><span class="text-xl font-bold" style="color: {primary};">{price}</span><button class="px-4 py-2 text-white text-sm font-semibold rounded-full" style="background: {primary};">Ajouter</button></div></div></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Boutique", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Découvrir", cta1_href="#products", cta2_text="Livraison", cta2_href="#shipping") + f"""
    <section id="products" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Produits phares</h2><div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-8">{products}</div></section>
    <section id="shipping" class="max-w-7xl mx-auto px-6 py-16"><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="bolt", title="Livraison rapide", description="Expédition sous 24h, livraison 2-3 jours.")}{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="shield", title="Paiement sécurisé", description="Transactions cryptées SSL, CB, PayPal.")}{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="check", title="Retours gratuits", description="30 jours pour changer d'avis. Retours gratuits.")}</div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + _cta_final(
        primary=primary, title="-10% sur votre première commande", description="Inscrivez-vous à notre newsletter.",
        button_text="S'inscrire", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_portfolio(*, business, title, tagline, sector, audience, locale,
                     primary, secondary, font_heading, brand_html, nav_html,
                     page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    projects = ""
    for name, desc_p, tags in [("Projet Alpha", "Refonte d'identité visuelle.", ["Branding", "UI/UX"]), ("Projet Beta", "App mobile pour startup santé.", ["Mobile", "Design"]), ("Projet Gamma", "Site e-commerce premium.", ["Web", "E-commerce"]), ("Projet Delta", "Campagne digitale 360°.", ["Marketing", "Strategy"])]:
        tag_html = "".join(f'<span class="text-xs px-2 py-1 rounded-full" style="color: {primary}; background: {primary_tint};">{t}</span>' for t in tags)
        projects += f'<article class="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-xl transition"><div class="h-64 bg-gray-100 flex items-center justify-center text-gray-400">Aperçu</div><div class="p-6"><h3 class="font-bold text-lg">{name}</h3><p class="text-gray-600 mt-1 text-sm">{desc_p}</p><div class="mt-3 flex gap-2">{tag_html}</div></div></article>'
    skills = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description="") for ic, t in [("camera", "Design"), ("code", "Développement"), ("target", "Stratégie"), ("star", "Branding")])
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Portfolio", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Voir mes projets", cta1_href="#projects", cta2_text="Me contacter", cta2_href="contact.html") + f"""
    <section id="projects" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Projets sélectionnés</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-8">{projects}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Compétences</h2><div class="grid grid-cols-2 md:grid-cols-4 gap-6">{skills}</div></section>
""" + _cta_final(primary=primary, title="Travaillons ensemble", description="Disponible pour de nouveaux projets.", button_text="Démarrer", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_realestate(*, business, title, tagline, sector, audience, locale,
                      primary, secondary, font_heading, brand_html, nav_html,
                      page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    listings = ""
    for name, details, price in [("Appartement T3 — Centre-ville", "78m² · 2 ch · Balcon", "285 000€"), ("Maison 5 pièces", "120m² · 4 ch · Jardin", "450 000€"), ("Studio meublé", "32m² · Refait à neuf", "145 000€")]:
        listings += f'<article class="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-xl transition"><div class="h-48 bg-gray-100 flex items-center justify-center text-gray-400">Photo</div><div class="p-6"><h3 class="font-bold text-lg">{name}</h3><p class="text-gray-600 mt-1 text-sm">{details}</p><div class="mt-3 text-2xl font-bold" style="color: {primary};">{price}</div></div></article>'
    services = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("home", "Achat", "Accompagnement complet."), ("trending", "Vente", "Estimation gratuite."), ("briefcase", "Location", "Gestion locative.")])
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Immobilier", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Voir les biens", cta1_href="#listings", cta2_text="Estimer", cta2_href="contact.html") + f"""
    <section id="listings" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Biens à la vente</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{listings}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{services}</div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + _cta_final(
        primary=primary, title="Estimez votre bien gratuitement", description="Estimation précise en moins de 24h.",
        button_text="Demander", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_health(*, business, title, tagline, sector, audience, locale,
                  primary, secondary, font_heading, brand_html, nav_html,
                  page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    specs = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("shield", "Consultation", "Diagnostic complet et plan de traitement."), ("heart", "Suivi", "Accompagnement régulier pour votre bien-être."), ("clock", "Urgences", "Disponibilité rapide pour situations urgentes."), ("users", "Prévention", "Bilans de santé et conseils personnalisés.")])
    addr = brief.get('contact', {}).get('address') or 'Adresse du cabinet'
    phone = brief.get('contact', {}).get('phone') or '01 23 45 67 89'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Santé", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Rendez-vous", cta1_href="contact.html", cta2_text="Services", cta2_href="#services") + f"""
    <section id="services" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos spécialités</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">{specs}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Informations pratiques</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8"><div class="bg-white p-8 rounded-2xl border border-gray-100"><div class="flex items-center gap-3" style="color: {primary};">{s('map')}<h3 class="font-bold">Adresse</h3></div><p class="text-gray-600 mt-3">{addr}</p></div><div class="bg-white p-8 rounded-2xl border border-gray-100"><div class="flex items-center gap-3" style="color: {primary};">{s('clock')}<h3 class="font-bold">Horaires</h3></div><p class="text-gray-600 mt-3">Lun-Ven: 9h-19h<br>Sam: 9h-13h</p></div><div class="bg-white p-8 rounded-2xl border border-gray-100"><div class="flex items-center gap-3" style="color: {primary};">{s('phone')}<h3 class="font-bold">Téléphone</h3></div><p class="text-gray-600 mt-3">{phone}</p></div></div></section>
""" + _cta_final(primary=primary, title="Prenez rendez-vous en ligne", description="Réservez votre créneau. Confirmation immédiate.", button_text="Réserver", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_fitness(*, business, title, tagline, sector, audience, locale,
                   primary, secondary, font_heading, brand_html, nav_html,
                   page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    plans = ""
    for name, price, features, popular in [("Essentiel", "29€", ["Accès salle 7j/7", "Vestiaires", "App mobile", "Sans engagement"], False), ("Premium", "49€", ["Tout Essentiel", "Cours illimités", "1 coaching/mois", "Sauna", "Nutrition"], True), ("Coaching", "89€", ["Tout Premium", "Coaching 4x/mois", "Plan sur-mesure", "Suivi nutrition", "Bilan mensuel"], False)]:
        badge = f'<span class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold text-white rounded-full" style="background: {primary};">POPULAIRE</span>' if popular else ""
        border = f'border-2 relative' if popular else 'border'
        border_color = f'border-color: {primary};' if popular else ''
        feat_html = "".join(f'<li class="flex items-center gap-2">{s("check")} {f}</li>' for f in features)
        plans += f'<article class="bg-white p-8 rounded-2xl {border}" style="{border_color}">{badge}<h3 class="font-bold text-xl">{name}</h3><div class="text-3xl font-extrabold mt-4" style="color: {primary};">{price}<span class="text-base font-normal text-gray-500">/mois</span></div><ul class="mt-6 space-y-3 text-gray-600 text-sm">{feat_html}</ul></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Fitness", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Voir les tarifs", cta1_href="#pricing", cta2_text="Essai gratuit", cta2_href="contact.html") + _stats_bar(
        primary=primary, stats=[("500+", "Membres"), ("30+", "Cours/sem"), ("15", "Coachs"), ("7j/7", "Ouvert")]) + f"""
    <section id="pricing" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos formules</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{plans}</div></section>
""" + _cta_final(primary=primary, title="Démarrez votre transformation", description="Première séance offerte.", button_text="Essai gratuit", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_beauty(*, business, title, tagline, sector, audience, locale,
                  primary, secondary, font_heading, brand_html, nav_html,
                  page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    services = ""
    for ic, t, d, price in [("scissors", "Coiffure", "Coupe, couleur, balayage.", "35€"), ("star", "Soins visage", "Soins sur-mesure.", "55€"), ("heart", "Massage", "Détente et bien-être.", "45€"), ("camera", "Maquillage", "Pour tous vos événements.", "40€"), ("star", "Onglerie", "Manucure et nail art.", "25€"), ("heart", "Spa", "Cure complète relaxation.", "80€")]:
        services += f'<article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition"><div class="w-12 h-12 rounded-xl flex items-center justify-center" style="color: {primary}; background: {primary_tint};">{s(ic)}</div><h3 class="text-xl font-bold mt-6">{t}</h3><p class="text-gray-600 mt-2">{d}</p><div class="mt-3 font-bold" style="color: {primary};">dès {price}</div></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Beauté", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Prestations", cta1_href="#services", cta2_text="Rendez-vous", cta2_href="contact.html") + f"""
    <section id="services" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos prestations</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{services}</div></section>
""" + _cta_final(primary=primary, title="Offre découverte -20%", description="Sur votre premier soin.", button_text="Réserver", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_legal(*, business, title, tagline, sector, audience, locale,
                 primary, secondary, font_heading, brand_html, nav_html,
                 page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    areas = ""
    for ic, t, d in [("briefcase", "Droit des affaires", "Conseil en droit commercial, créations d'entreprises."), ("shield", "Droit du travail", "Litiges prud'homaux, conventions collectives."), ("home", "Droit immobilier", "Baux, acquisitions, ventes immobilières."), ("users", "Droit de la famille", "Divorce, succession, tutelle.")]:
        areas += f'<article class="bg-white p-8 rounded-2xl border border-gray-100"><div class="flex items-center gap-3" style="color: {primary};">{s(ic)}<h3 class="text-xl font-bold">{t}</h3></div><p class="text-gray-600 mt-3">{d}</p></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Cabinet juridique", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Domaines", cta1_href="#expertise", cta2_text="Consultation", cta2_href="contact.html") + f"""
    <section id="expertise" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Domaines d'expertise</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-8">{areas}</div></section>
""" + _stats_bar(primary=primary, stats=[("25+", "Ans d'expérience"), ("1200+", "Dossiers"), ("95%", "Réussite")]) + _cta_final(
        primary=primary, title="Première consultation gratuite", description="Évaluez votre situation. Confidentialité garantie.",
        button_text="Rendez-vous", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_tech(*, business, title, tagline, sector, audience, locale,
                primary, secondary, font_heading, brand_html, nav_html,
                page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    features = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("bolt", "Temps réel", "Sync instantanée."), ("shield", "Sécurité", "Chiffrement bout-en-bout."), ("code", "API ouverte", "Intégration facile."), ("trending", "Analytics", "Dashboards en temps réel."), ("users", "Collaboration", "Rôles et partage."), ("check", "Automatisation", "Workflows personnalisés.")])
    plans = ""
    for name, price, features_list in [("Starter", "19€", ["5 utilisateurs", "10GB", "Support email"]), ("Pro", "49€", ["25 utilisateurs", "100GB", "API complète", "Support prioritaire"]), ("Enterprise", "Sur devis", ["Illimité", "SSO & SAML", "Account manager"])]:
        feat_html = "".join(f'<li class="flex items-center gap-2">{s("check")} {f}</li>' for f in features_list)
        plans += f'<article class="bg-white p-8 rounded-2xl border border-gray-100"><h3 class="font-bold text-xl">{name}</h3><div class="text-3xl font-extrabold mt-4" style="color: {primary};">{price}</div><ul class="mt-6 space-y-3 text-gray-600 text-sm">{feat_html}</ul></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Tech / SaaS", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Fonctionnalités", cta1_href="#features", cta2_text="Démo", cta2_href="contact.html") + f"""
    <section id="features" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Fonctionnalités</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{features}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Tarifs</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{plans}</div></section>
""" + _cta_final(primary=primary, title="14 jours gratuits", description="Aucune CB requise. Configuration en 2 min.", button_text="Démarrer", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_construction(*, business, title, tagline, sector, audience, locale,
                        primary, secondary, font_heading, brand_html, nav_html,
                        page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    services = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("home", "Construction neuve", "Maisons et bâtiments clé en main."), ("bolt", "Rénovation", "Rénovation complète et partielle."), ("shield", "Travaux spécialisés", "Maçonnerie, toiture, électricité."), ("briefcase", "Conseil & études", "Études techniques et devis.")])
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Construction", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Services", cta1_href="#services", cta2_text="Devis gratuit", cta2_href="contact.html") + f"""
    <section id="services" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos services</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">{services}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos réalisations</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8"><div class="bg-gray-100 rounded-2xl h-64 flex items-center justify-center text-gray-400">Chantier 1</div><div class="bg-gray-100 rounded-2xl h-64 flex items-center justify-center text-gray-400">Chantier 2</div><div class="bg-gray-100 rounded-2xl h-64 flex items-center justify-center text-gray-400">Chantier 3</div></div></section>
""" + _cta_final(primary=primary, title="Devis gratuit", description="Réponse sous 48h avec estimation détaillée.", button_text="Obtenir un devis", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_education(*, business, title, tagline, sector, audience, locale,
                     primary, secondary, font_heading, brand_html, nav_html,
                     page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    courses = ""
    for ic, t, d, price in [("code", "Dév web", "HTML, CSS, JS, React. 12 semaines.", "3 500€"), ("target", "Marketing digital", "SEO, SEA, réseaux sociaux. 8 semaines.", "2 800€"), ("star", "Design UX/UI", "Figma, prototypage. 10 semaines.", "3 200€")]:
        courses += f'<article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition"><div class="w-12 h-12 rounded-xl flex items-center justify-center" style="color: {primary}; background: {primary_tint};">{s(ic)}</div><h3 class="text-xl font-bold mt-6">{t}</h3><p class="text-gray-600 mt-2">{d}</p><div class="mt-3 font-bold" style="color: {primary};">{price}</div></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Formation", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Cours", cta1_href="#courses", cta2_text="S'inscrire", cta2_href="contact.html") + f"""
    <section id="courses" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos formations</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{courses}</div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + _cta_final(
        primary=primary, title="Inscrivez-vous à la prochaine session", description="Places limitées.",
        button_text="S'inscrire", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_consulting(*, business, title, tagline, sector, audience, locale,
                      primary, secondary, font_heading, brand_html, nav_html,
                      page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    areas = ""
    for ic, t, d in [("trending", "Stratégie", "Analyse et plan de croissance."), ("briefcase", "Transformation digitale", "Digitalisation et choix tech."), ("target", "Performance", "Optimisation des processus."), ("users", "Ressources humaines", "Gestion des talents et culture.")]:
        areas += f'<article class="bg-white p-8 rounded-2xl border border-gray-100"><div class="flex items-center gap-3" style="color: {primary};">{s(ic)}<h3 class="text-xl font-bold">{t}</h3></div><p class="text-gray-600 mt-3">{d}</p></article>'
    steps = ""
    for num, t, d in [("1", "Diagnostic", "Analyse complète."), ("2", "Stratégie", "Plan d'action clair."), ("3", "Exécution", "Mise en œuvre et suivi."), ("4", "Résultats", "Mesure de l'impact.")]:
        steps += f'<div class="text-center"><div class="w-16 h-16 mx-auto rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background: {primary};">{num}</div><h3 class="font-bold mt-4">{t}</h3><p class="text-gray-600 mt-2 text-sm">{d}</p></div>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Conseil", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Services", cta1_href="#services", cta2_text="Consultation", cta2_href="contact.html") + f"""
    <section id="services" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Domaines de conseil</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-8">{areas}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Notre méthode</h2><div class="grid grid-cols-1 md:grid-cols-4 gap-8">{steps}</div></section>
""" + _cta_final(primary=primary, title="Planifions votre prochaine étape", description="Premier échange offert.", button_text="Réserver", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_travel(*, business, title, tagline, sector, audience, locale,
                  primary, secondary, font_heading, brand_html, nav_html,
                  page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    dests = ""
    for name, details, price in [("Bali, Indonésie", "7j · Tout inclus · 4*", "1 290€"), ("Santorin, Grèce", "5j · Demi-pension · Caldera", "890€"), ("Marrakech, Maroc", "4j · Riad traditionnel", "590€")]:
        dests += f'<article class="bg-white rounded-2xl border border-gray-100 overflow-hidden hover:shadow-xl transition"><div class="h-56 bg-gray-100 flex items-center justify-center text-gray-400">Photo</div><div class="p-6"><h3 class="font-bold text-lg">{name}</h3><p class="text-gray-600 mt-1 text-sm">{details}</p><div class="mt-3 text-xl font-bold" style="color: {primary};">{price}</div></div></article>'
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Voyage", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Destinations", cta1_href="#destinations", cta2_text="Réserver", cta2_href="contact.html") + f"""
    <section id="destinations" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Destinations populaires</h2><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{dests}</div></section>
    <section class="max-w-7xl mx-auto px-6 py-16"><div class="grid grid-cols-1 md:grid-cols-3 gap-8">{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="map", title="Sur-mesure", description="Itinéraires personnalisés.")}{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="shield", title="Sérénité", description="Assurance et assistance 24/7.")}{_feature_card(primary=primary, primary_tint=primary_tint, icon_name="star", title="Expériences uniques", description="Activités exclusives.")}</div></section>
""" + _cta_final(primary=primary, title="Réservez votre prochain voyage", description="Voyages sur-mesure à prix imbattables.", button_text="Réserver", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_automotive(*, business, title, tagline, sector, audience, locale,
                      primary, secondary, font_heading, brand_html, nav_html,
                      page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    services = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("bolt", "Réparation", "Toutes marques, devis gratuit."), ("shield", "Entretien", "Vidange, freins, pneus, CT."), ("clock", "Dépannage", "Assistance 7j/7 sur la région."), ("check", "Carrosserie", "Réparation et peinture carrosserie.")])
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label="Automobile", title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Services", cta1_href="#services", cta2_text="Devis", cta2_href="contact.html") + f"""
    <section id="services" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Nos services</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">{services}</div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + _cta_final(
        primary=primary, title="Devis gratuit", description="Diagnostic offert pour toute réparation.",
        button_text="Prendre RDV", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


def _build_default(*, business, title, tagline, sector, audience, locale,
                   primary, secondary, font_heading, brand_html, nav_html,
                   page, brief, page_seo_desc, primary_tint, s) -> str:
    desc = brief.get('description') or tagline
    features = "".join(_feature_card(primary=primary, primary_tint=primary_tint, icon_name=ic, title=t, description=d) for ic, t, d in [("target", "Expertise", f"Maîtrise des défis du secteur {sector}."), ("users", "Personnalisé", "Suivi dédié et interlocuteur unique."), ("shield", "Qualité", "Standards élevés et satisfaction garantie."), ("bolt", "Réactivité", "Délai de réponse de 24h.")])
    faq = _faq_section(primary=primary, sector=sector, questions=[(f"Services en {sector} ?", "Gamme complète adaptée à vos besoins."), ("Délais ?", "Réponse sous 24h, planning clair."), ("Devis ?", "Contactez-nous pour un devis gratuit."), ("Maintenance ?", "Contrats adaptés à vos besoins."), ("Zone ?", "Intervention partout en France.")])
    return _head(title=title, business=business, page_seo_desc=page_seo_desc, locale=locale,
                 primary=primary, secondary=secondary, font_heading=font_heading) + _header(
        brand_html=brand_html, nav_html=nav_html) + _hero(
        label=sector.title(), title=title, description=desc, primary=primary, primary_tint=primary_tint,
        cta1_text="Démarrer", cta1_href="contact.html", cta2_text="En savoir plus", cta2_href="#features") + _stats_bar(
        primary=primary, stats=[("10+", "Ans"), ("500+", "Clients"), ("98%", "Satisfaction"), ("24h", "Réponse")]) + f"""
    <section id="features" class="max-w-7xl mx-auto px-6 py-16"><h2 class="text-3xl font-bold text-center mb-12" style="color: {primary};">Pourquoi nous choisir</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">{features}</div></section>
""" + _testimonials_dark(primary=primary, business=business, sector=sector) + faq + _cta_final(
        primary=primary, title="Prêt à démarrer ?", description="Consultation gratuite. Réponse sous 24h.",
        button_text="Demander un devis", button_href="contact.html") + "  </main>\n" + _footer(business=business, sector=sector, audience=audience)


_BUILDERS = {
    "restaurant": _build_restaurant,
    "ecommerce": _build_ecommerce,
    "portfolio": _build_portfolio,
    "realestate": _build_realestate,
    "health": _build_health,
    "fitness": _build_fitness,
    "beauty": _build_beauty,
    "legal": _build_legal,
    "tech": _build_tech,
    "construction": _build_construction,
    "education": _build_education,
    "consulting": _build_consulting,
    "travel": _build_travel,
    "automotive": _build_automotive,
}


def build_sector_html(
    sector_key: str,
    *,
    business: str, title: str, tagline: str, sector: str, audience: str,
    locale: str, primary: str, secondary: str, font_heading: str,
    brand_html: str, nav_html: str, page: dict[str, Any], brief: dict[str, Any],
    page_seo_desc: str,
) -> str:
    builder = _BUILDERS.get(sector_key, _build_default)
    s = _svg
    primary_tint = primary + "15"
    return builder(
        business=business, title=title, tagline=tagline, sector=sector,
        audience=audience, locale=locale, primary=primary, secondary=secondary,
        font_heading=font_heading, brand_html=brand_html, nav_html=nav_html,
        page=page, brief=brief, page_seo_desc=page_seo_desc, primary_tint=primary_tint, s=s,
    )
