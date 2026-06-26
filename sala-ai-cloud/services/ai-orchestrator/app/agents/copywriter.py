from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentInput, BaseAgent


class CopywriterAgent(BaseAgent):
    name = "copywriter"
    default_temperature = 0.7
    default_max_tokens = 12000
    use_thinking = True

    def system_prompt(self, inp: AgentInput) -> str:
        return (
            "Tu es un Copywriter senior, expert en conversion et SEO. "
            "Tu rédiges des textes marketing riches, détaillés et persuasifs dans la langue demandée, "
            "avec un ton adapté au brief. Pas de bullshit corporate. "
            "Chaque section doit avoir du contenu substantiel — pas de phrases génériques.\n"
            "Réponds STRICTEMENT en JSON valide (objet unique).\n"
            "Schéma :\n"
            "{\n"
            '  "pages": [\n'
            "    {\n"
            '      "slug": "home",\n'
            '      "title": "string",\n'
            '      "sections": [\n'
            '        { "type": "hero", "title":"...", "subtitle":"... (2-3 phrases détaillées)", "body":"... (paragraphe d\'introduction 3-5 phrases)", "cta_primary":"...", "cta_secondary":"..." },\n'
            '        { "type": "features", "title":"...", "intro":"... (1-2 phrases)", "items":[{"title":"...","desc":"... (2-3 phrases détaillées)","icon":"...","points":["...","..."]}] },\n'
            '        { "type": "about", "title":"...", "body":"... (3-5 paragraphes riches)", "values":["...","..."] },\n'
            '        { "type": "services", "title":"...", "items":[{"title":"...","desc":"... (3-4 phrases)","features":["...","..."]}] },\n'
            '        { "type": "testimonials", "title":"...", "items":[{"author":"...","role":"...","quote":"... (2-3 phrases)","rating":5}] },\n'
            '        { "type": "pricing", "title":"...", "plans":[{"name":"...","price":"...","period":"...","features":["...","...","..."],"cta":"...","highlighted":false}] },\n'
            '        { "type": "faq", "title":"...", "items":[{"q":"...","a":"... (2-4 phrases détaillées)"}] },\n'
            '        { "type": "stats", "title":"...", "items":[{"value":"...","label":"...","desc":"..."}] },\n'
            '        { "type": "process", "title":"...", "steps":[{"number":1,"title":"...","desc":"... (2-3 phrases)"}] },\n'
            '        { "type": "cta_banner", "title":"...", "subtitle":"... (2 phrases)", "body":"... (1-2 phrases)", "cta":"..." },\n'
            '        { "type": "contact", "title":"...", "subtitle":"...", "body":"... (2-3 phrases)" }\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Règles de structure :\n"
            "- Si le brief spécifie stack == 'onepage' : génère EXACTEMENT une seule page avec slug 'home'. Toutes les sections (hero, features, about, testimonials, pricing, faq, cta_banner, contact) doivent être sur cette unique page.\n"
            "- Si le brief spécifie stack == 'multipage' : génère une page par élément listé dans 'Pages demandées'. Répartis les sections de manière logique et pertinente sur ces différentes pages (4 à 7 sections par page, chaque page ayant ses propres sections spécifiques).\n\n"
            "RÈGLES DE RICHESSE DU CONTENU (CRITIQUE) :\n"
            "- Chaque section hero doit avoir un title percutant, un subtitle de 2-3 phrases, et un body d'introduction de 3-5 phrases.\n"
            "- Chaque section features doit avoir MINIMUM 4 items, chacun avec 2-3 phrases de description et 2-3 points clés.\n"
            "- Chaque section about doit avoir 3-5 paragraphes développés (minimum 150 mots total).\n"
            "- Chaque section testimonials doit avoir MINIMUM 3 témoignages avec citations de 2-3 phrases.\n"
            "- Chaque section pricing doit avoir 3-4 plans avec 4-6 features chacun.\n"
            "- Chaque section faq doit avoir MINIMUM 5 questions avec réponses de 2-4 phrases.\n"
            "- Adapte le contenu au secteur, à l'audience et aux objectifs du brief. Utilise des arguments spécifiques, des chiffres, des exemples concrets.\n"
            "- JAMAIS de contenu générique comme 'Nous offrons des services de qualité'. Toujours du contenu spécifique au secteur et à la marque."
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
        sector = brief.get("sector", "notre secteur")
        tagline = brief.get("tagline") or brief.get("description") or "Votre nouveau site web professionnel."
        audience = brief.get("target_audience", "nos clients")

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
                        "title": f"{name} — L'expert en {sector}",
                        "subtitle": tagline,
                        "body": f"Chez {name}, nous accompagnons {audience} avec des solutions sur-mesure dans le secteur {sector}. Notre approche combine expertise technique et compréhension fine de vos besoins pour deliver des résultats concrets et durables.",
                        "cta_primary": "Demander un devis",
                        "cta_secondary": "Découvrir nos services",
                    },
                    {
                        "type": "stats",
                        "title": "Notre impact en chiffres",
                        "items": [
                            {"value": "10+", "label": "Années d'expérience", "desc": f"Une décennie d'expertise en {sector}"},
                            {"value": "500+", "label": "Clients satisfaits", "desc": "Une clientèle fidèle et grandissante"},
                            {"value": "98%", "label": "Taux de satisfaction", "desc": "Des résultats qui parlent d'eux-mêmes"},
                            {"value": "24h", "label": "Délai de réponse", "desc": "Une réactivité exemplaire"},
                        ],
                    },
                    {
                        "type": "features",
                        "title": "Pourquoi nous choisir",
                        "intro": f"Nous offrons bien plus qu'un service standard en {sector}. Voici ce qui nous distingue.",
                        "items": [
                            {"title": "Expertise spécialisée", "desc": f"Notre équipe maîtrise parfaitement les défis spécifiques du secteur {sector}, avec une expérience terrain éprouvée.", "icon": "target", "points": ["Connaissance approfondie du marché", "Solutions adaptées à vos contraintes", "Veille permanente sur les tendances"]},
                            {"title": "Accompagnement personnalisé", "desc": "Chaque client bénéficie d'un suivi dédié avec un interlocuteur unique qui comprend vos enjeux et vos objectifs.", "icon": "users", "points": ["Interlocuteur unique et dédié", "Suivi régulier et transparent", "Solutions sur-mesure"]},
                            {"title": "Qualité garantie", "desc": "Nous nous engageons sur des résultats mesurables avec des standards qualité élevés et une satisfaction client prioritaire.", "icon": "shield", "points": ["Standards qualité élevés", "Engagement sur les résultats", "Satisfaction client garantie"]},
                            {"title": "Réactivité et fiabilité", "desc": "Notre équipe réagit rapidement à vos demandes avec un délai de réponse moyen de 24 heures et une disponibilité adaptée.", "icon": "bolt", "points": ["Délai de réponse < 24h", "Disponibilité adaptée", "Communication fluide"]},
                        ],
                    },
                    {
                        "type": "process",
                        "title": "Notre méthode de travail",
                        "steps": [
                            {"number": 1, "title": "Consultation gratuite", "desc": f"Nous analysons vos besoins spécifiques en {sector} lors d'un échange approfondi pour comprendre vos enjeux."},
                            {"number": 2, "title": "Proposition sur-mesure", "desc": "Nous élaborons une solution personnalisée avec un devis détaillé et un planning clair."},
                            {"number": 3, "title": "Réalisation et suivi", "desc": "Notre équipe met en œuvre la solution avec un suivi régulier et des points d'étape."},
                            {"number": 4, "title": "Livraison et support", "desc": "Nous livrons le projet dans les délais et assurons un support continu après livraison."},
                        ],
                    },
                    {
                        "type": "testimonials",
                        "title": "Ce que disent nos clients",
                        "items": [
                            {"author": "Marie Dubois", "role": "Directrice, Cabinet Dubois", "quote": f"Travailler avec {name} a transformé notre approche du {sector}. Professionnalisme et résultats au rendez-vous.", "rating": 5},
                            {"author": "Thomas Laurent", "role": "Gérant, LT Solutions", "quote": "Une équipe à l'écoute, réactive et compétente. Je recommande vivement leurs services.", "rating": 5},
                            {"author": "Sophie Martin", "role": "Responsable marketing", "quote": "Le suivi est excellent et les résultats ont dépassé nos attentes. Un vrai partenaire de confiance.", "rating": 5},
                        ],
                    },
                    {
                        "type": "faq",
                        "title": "Questions fréquentes",
                        "items": [
                            {"q": f"Quels services proposez-vous en {sector} ?", "a": f"Nous proposons une gamme complète de services en {sector}, adaptés aux besoins de chaque client. Contactez-nous pour un devis personnalisé."},
                            {"q": "Quels sont vos délais d'intervention ?", "a": "Notre délai de réponse moyen est de 24 heures. Pour les projets, nous établissons un planning clair lors de la consultation."},
                            {"q": "Intervenez-vous dans toute la France ?", "a": "Oui, nous intervenons partout en France et proposons également des services à distance selon vos besoins."},
                            {"q": "Comment obtenir un devis ?", "a": "Il vous suffit de nous contacter via le formulaire de contact ou par téléphone. Nous vous répondons sous 24h avec une proposition détaillée."},
                            {"q": "Proposez-vous des contrats de maintenance ?", "a": "Oui, nous proposons des contrats de maintenance et de support adaptés à vos besoins pour assurer la pérennité de vos projets."},
                        ],
                    },
                    {
                        "type": "cta_banner",
                        "title": "Prêt à démarrer votre projet ?",
                        "subtitle": "Contactez-nous aujourd'hui pour une consultation gratuite.",
                        "body": "Notre équipe est prête à répondre à vos questions et à vous accompagner dans votre projet.",
                        "cta": "Demander un devis gratuit",
                    },
                    {
                        "type": "contact",
                        "title": "Contactez-nous",
                        "subtitle": "Nous répondons sous 24h.",
                        "body": f"Que vous ayez une question sur nos services en {sector} ou que vous souhaitiez démarrer un projet, notre équipe est à votre écoute.",
                    },
                ]
                if stack != "onepage":
                    sections = sections[:3] + sections[5:]

                fallback_pages.append({"slug": "home", "title": name, "sections": sections})
            elif p == "about":
                fallback_pages.append({
                    "slug": "about",
                    "title": f"{name} - À propos",
                    "sections": [
                        {"type": "hero", "title": f"À propos de {name}", "subtitle": f"Votre partenaire de confiance en {sector}", "body": f"Fondée avec la volonté de transformer le secteur {sector}, {name} s'est imposée comme une référence auprès de {audience}.", "cta_primary": "Nous contacter", "cta_secondary": ""},
                        {"type": "about", "title": "Notre histoire", "body": f"L'histoire de {name} commence avec une passion : offrir un service d'excellence en {sector}. Au fil des années, nous avons construit une réputation solide grâce à notre engagement envers la qualité et la satisfaction client.\n\nAujourd'hui, nous accompagnons des centaines de clients avec une approche personnalisée et des solutions innovantes. Notre équipe d'experts met tout en œuvre pour répondre à vos besoins les plus spécifiques.\n\nNotre mission est simple : vous fournir des résultats concrets et durables, tout en bâtissant une relation de confiance sur le long terme.", "values": ["Excellence", "Transparence", "Innovation", "Proximité client"]},
                        {"type": "testimonials", "title": "Ils nous font confiance", "items": [
                            {"author": "Marie Dubois", "role": "Directrice", "quote": f"Une collaboration fructueuse avec {name} depuis plusieurs années.", "rating": 5},
                            {"author": "Thomas Laurent", "role": "Gérant", "quote": "Des professionnels à l'écoute et engagés.", "rating": 5},
                        ]},
                        {"type": "contact", "title": "Contactez-nous", "subtitle": "Nous répondons sous 24h.", "body": "Une question ? N'hésitez pas à nous contacter."},
                    ],
                })
            elif p == "services":
                fallback_pages.append({
                    "slug": "services",
                    "title": f"{name} - Services",
                    "sections": [
                        {"type": "hero", "title": f"Nos services en {sector}", "subtitle": "Des solutions sur-mesure pour vos besoins", "body": f"Découvrez l'ensemble de nos services en {sector}, conçus pour répondre aux défis spécifiques de {audience}.", "cta_primary": "Demander un devis", "cta_secondary": ""},
                        {"type": "services", "title": "Nos prestations", "items": [
                            {"title": "Service principal", "desc": f"Notre service cœur de métier en {sector}, adapté à vos besoins spécifiques avec un suivi personnalisé.", "features": ["Diagnostic personnalisé", "Mise en œuvre professionnelle", "Suivi et optimisation continue"]},
                            {"title": "Accompagnement", "desc": "Un accompagnement complet de A à Z avec un interlocuteur dédié pour garantir la réussite de votre projet.", "features": ["Consultation stratégique", "Plan d'action détaillé", "Support continu"]},
                            {"title": "Maintenance et support", "desc": "Des contrats de maintenance flexibles pour assurer la pérennité et la performance de vos solutions.", "features": ["Maintenance préventive", "Support technique", "Mises à jour régulières"]},
                        ]},
                        {"type": "process", "title": "Comment nous travaillons", "steps": [
                            {"number": 1, "title": "Analyse", "desc": "Nous commençons par analyser vos besoins en profondeur."},
                            {"number": 2, "title": "Proposition", "desc": "Nous vous soumettons une proposition détaillée et transparente."},
                            {"number": 3, "title": "Réalisation", "desc": "Nous mettons en œuvre la solution avec rigueur et professionnalisme."},
                        ]},
                        {"type": "faq", "title": "Questions sur nos services", "items": [
                            {"q": "Comment se déroule la première consultation ?", "a": "La première consultation est gratuite et sans engagement. Nous analysons vos besoins et vous proposons une solution adaptée."},
                            {"q": "Proposez-vous des forfaits ?", "a": "Oui, nous proposons plusieurs forfaits adaptés à différents besoins et budgets. Contactez-nous pour plus d'informations."},
                        ]},
                        {"type": "contact", "title": "Demandez un devis", "subtitle": "Nous répondons sous 24h.", "body": "Contactez-nous pour obtenir un devis personnalisé pour votre projet."},
                    ],
                })
            else:
                fallback_pages.append({
                    "slug": p,
                    "title": f"{name} - {p.capitalize()}",
                    "sections": [
                        {"type": "hero", "title": p.capitalize(), "subtitle": f"Découvrez notre page {p}.", "body": f"Des informations détaillées sur {p} chez {name}.", "cta_primary": "Nous contacter", "cta_secondary": ""},
                        {"type": "contact", "title": "Contact", "subtitle": "Contactez-nous pour toute question.", "body": "Notre équipe est à votre disposition pour répondre à toutes vos questions."},
                    ],
                })
        return {"pages": fallback_pages}
