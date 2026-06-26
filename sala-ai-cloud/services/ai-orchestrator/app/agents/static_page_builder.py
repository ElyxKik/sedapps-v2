from __future__ import annotations

import json
import re
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage
from app.agents.sector_templates import build_sector_html, detect_sector
from app.llm.deepseek import LLMError

_HTML_FENCE_RE = re.compile(r"```html\s*([\s\S]*?)```", re.IGNORECASE)
_JSON_FENCE_RE = re.compile(r"```json\s*([\s\S]*?)```", re.IGNORECASE)


class StaticPageBuilderAgent(BaseAgent):
    name = "static_page_builder"
    default_temperature = 0.5
    default_max_tokens = 16000
    use_thinking = True

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es un senior frontend designer spécialisé en pages statiques premium de très haute qualité.

Tu génères UNE SEULE PAGE HTML à la fois, jamais tout le site.
Tu DOIS utiliser Tailwind CSS CDN pour toute la mise en page (classes utilitaires directement sur les éléments HTML).

⚠ RÈGLES ABSOLUES — DESIGN TOKENS :
- Tu DOIS utiliser EXACTEMENT les couleurs fournies dans les design tokens (palette.primary, palette.secondary, etc.).
- Tu DOIS utiliser EXACTEMENT la police fournie dans typography.heading pour les titres et typography.body pour le texte.
- Si un logo_url est fourni dans les design tokens ou le brief, tu DOIS l'afficher dans le header à la place du nom de la marque en texte.
- Configure Tailwind avec les couleurs du design tokens via un bloc <script> dans le <head> :
  tailwind.config = { theme: { extend: { colors: { brand: '#hex', 'brand-secondary': '#hex' } }, fontFamily: { heading: ['FontName', 'sans-serif'] } } }
- Utilise les classes bg-brand, text-brand, font-heading etc. dans tout le HTML.
- JAMAIS utiliser des couleurs par défaut d'indigo/violet/blue de Tailwind. UNIQUEMENT les couleurs du design tokens.

Contraintes HTML :
- Document HTML complet d'exception avec <!doctype html>, head, body.
- Inclure dans le <head> : <script src="https://cdn.tailwindcss.com"></script>, <link rel="stylesheet" href="./styles.css">, <script src="./script.js" defer></script>
- Design sur-mesure pour la marque, l'audience et l'objectif du brief. Aucune section générique.
- Header sticky et Footer cohérents avec la navigation globale du site.
- Icônes SVG inline professionnelles pour un rendu ultra-premium.
- Jamais d'emoji sauf demande explicite dans le brief.
- Pas de lorem ipsum, pas de placeholder, pas de TODO. Contenu entièrement rédigé, persuasif, adapté au secteur.
- Si brief.premium == true : esthétique maximale, micro-détails, storytelling immersif.

EXIGENCES DE RICHESSE DU CONTENU (CRITIQUE) :
- Chaque page doit contenir MINIMUM 4 sections substantielles (hors header/footer).
- Chaque section hero doit avoir un titre percutant, un sous-titre de 2-3 phrases, et un paragraphe d'introduction de 3-5 phrases.
- Chaque section features/services doit avoir MINIMUM 4 items avec 2-3 phrases de description chacun.
- Chaque section about doit avoir MINIMUM 3 paragraphes développés (150+ mots).
- Chaque section testimonials doit avoir MINIMUM 3 témoignages avec citations de 2-3 phrases.
- Chaque section FAQ doit avoir MINIMUM 5 questions avec réponses de 2-4 phrases.
- Chaque section pricing doit avoir 3-4 plans avec 4-6 features chacun.
- Le contenu textuel total de chaque page doit être d'au MINIMUM 800 mots.
- Utilise le contenu fourni par le copywriter comme base et DÉVELOPPE-LE davantage dans le HTML.
- Ajoute des preuves sociales, des chiffres clés, des statistiques, des arguments spécifiques au secteur.
- Varie les layouts de sections : grilles, colonnes, cartes, timelines, accordions, tableaux.
- Inclus des transitions visuelles entre sections (couleurs de fond alternées, séparateurs élégants).

FORMAT DE RÉPONSE OBLIGATOIRE — deux blocs séparés, dans cet ordre exact :

```html
<!doctype html>
<html lang="fr">
...tout le HTML...
</html>
```

```json
{"path": "index.html", "sections": [{"id": "hero", "component": "HeroSplit", "title": "...", "enabled": true}]}
```

IMPORTANT : Le HTML doit être dans le bloc ```html et les métadonnées dans le bloc ```json. Ne mets JAMAIS le HTML dans du JSON.
""".strip()

    def user_prompt(self, inp: AgentInput) -> str:
        brief = inp.context.get("brief", {})
        plan = inp.context.get("site_planner", {})
        designer = inp.context.get("designer", {})
        copywriter = inp.context.get("copywriter", {})
        seo = inp.context.get("seo", {})
        strategy = inp.context.get("strategy_director", {})
        ux = inp.context.get("ux_architect", {})
        page = inp.params.get("page", {})

        # Extract design constraints explicitly
        palette = (designer.get("palette") or {}) if isinstance(designer, dict) else {}
        typo = (designer.get("typography") or {}) if isinstance(designer, dict) else {}
        logo_url = designer.get("logo_url") or brief.get("logo_url") or brief.get("identity", {}).get("logo_url")
        primary = palette.get("primary") or brief.get("primary_color") or brief.get("brand", {}).get("primary_color")
        secondary = palette.get("secondary") or brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color")
        font_heading = typo.get("heading") or brief.get("font_style") or brief.get("font_pref") or brief.get("brand", {}).get("font_heading")
        font_body = typo.get("body") or font_heading

        design_constraints = []
        if primary:
            design_constraints.append(f"⚠ COULEUR PRIMAIRE OBLIGATOIRE : {primary} — utilise-la pour bg-brand, text-brand, boutons, liens.")
        if secondary:
            design_constraints.append(f"⚠ COULEUR SECONDAIRE OBLIGATOIRE : {secondary} — utilise-la pour brand-secondary.")
        if font_heading:
            design_constraints.append(f"⚠ POLICE TITRES OBLIGATOIRE : {font_heading} — utilise font-heading sur tous les titres.")
        if font_body:
            design_constraints.append(f"⚠ POLICE TEXTE OBLIGATOIRE : {font_body} — utilise-la pour le body.")
        if logo_url:
            design_constraints.append(f"⚠ LOGO OBLIGATOIRE : Affiche <img src=\"{logo_url}\" alt=\"logo\"> dans le header au lieu du texte.")
        design_constraints.append("⚠ Configure Tailwind avec: tailwind.config = { theme: { extend: { colors: { brand: '" + (primary or "#000") + "', 'brand-secondary': '" + (secondary or "#666") + "' } }, fontFamily: { heading: ['" + (font_heading or "Inter") + "', 'sans-serif'] } } }")

        # Extraire les métadonnées SEO spécifiques à cette page si disponibles
        page_path = str(page.get("path") or "index.html")
        page_seo = {}
        for meta in (seo.get("pages") or []):
            if isinstance(meta, dict) and str(meta.get("path") or "") == page_path:
                page_seo = meta
                break
        if not page_seo and isinstance(seo.get("meta"), dict):
            page_seo = seo.get("meta", {})

        parts = [
            f"Langue : {inp.locale}\n",
            f"Brief :\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n",
            f"Design tokens (utilise EXACTEMENT ces couleurs et polices) :\n{json.dumps(designer, ensure_ascii=False, indent=2)}\n",
            f"CONTRAINTES DESIGN OBLIGATOIRES :\n" + "\n".join(design_constraints) + "\n",
            f"Copywriter (contenu à intégrer directement) :\n{json.dumps(copywriter, ensure_ascii=False, indent=2)}\n",
            f"Plan global du site :\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n",
            f"Page à générer :\n{json.dumps(page, ensure_ascii=False, indent=2)}\n",
        ]
        if page_seo:
            parts.append(f"SEO pour cette page :\n{json.dumps(page_seo, ensure_ascii=False, indent=2)}\n")
        if strategy:
            # Extraire uniquement les champs clés pour ne pas surcharger le prompt
            strategy_summary = {
                k: strategy.get(k)
                for k in ("positioning", "usp", "emotional_angle", "tone_of_voice", "target_persona")
                if strategy.get(k)
            }
            if strategy_summary:
                parts.append(f"Stratégie de marque (applique ce positionnement dans le texte) :\n{json.dumps(strategy_summary, ensure_ascii=False, indent=2)}\n")
        if ux:
            ux_summary = {
                k: ux.get(k)
                for k in ("conversion_points", "user_flows", "cta_hierarchy", "trust_signals")
                if ux.get(k)
            }
            if ux_summary:
                parts.append(f"Architecture UX (respecte cette hiérarchie de conversion) :\n{json.dumps(ux_summary, ensure_ascii=False, indent=2)}\n")

        parts.append(
            "Génère cette page en DEUX blocs séparés : ```html ... ``` puis ```json ... ```"
        )
        return "\n".join(parts)

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        import time
        t0 = time.perf_counter()
        warnings: list[str] = []
        max_retries = 2
        brief = inp.context.get("brief", {})
        is_premium = bool(brief.get("premium"))
        # Premium pages are richer (more sections, more content) — need more tokens
        effective_max_tokens = 24000 if is_premium else self.default_max_tokens
        messages = [
            {"role": "system", "content": self.system_prompt(inp)},
            {"role": "user", "content": self.user_prompt(inp)},
        ]
        tokens_prompt = tokens_completion = 0
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                resp = await self.client.chat(
                    messages=messages,
                    temperature=self.default_temperature,
                    max_tokens=effective_max_tokens,
                    thinking=self.use_thinking,
                    response_format_json=False,  # plain text — HTML can't go in JSON mode
                )
                tokens_prompt += resp.usage.prompt_tokens
                tokens_completion += resp.usage.completion_tokens

                # Detect truncated HTML (missing </html>)
                if "</html>" not in resp.content.lower():
                    warnings.append("Response appears truncated (no </html> tag) — retrying")
                    if attempt < max_retries:
                        messages.append({"role": "assistant", "content": resp.content})
                        messages.append({
                            "role": "user",
                            "content": (
                                "Le HTML est TRONQUÉ — la réponse s'est arrêtée avant </html>. "
                                "Reprends depuis le point de coupure et termine le document HTML complet. "
                                "Ne répète pas le début, continue uniquement à partir de la coupure."
                            ),
                        })
                        continue

                try:
                    data = self._parse_dual_block(resp.content, inp)
                    return AgentOutput(
                        agent=self.name,
                        status="ok",
                        data=data,
                        tokens=TokenUsage(prompt=tokens_prompt, completion=tokens_completion),
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        model=resp.model,
                        warnings=warnings,
                    )
                except (ValueError, KeyError) as parse_err:
                    last_error = parse_err
                    if attempt < max_retries:
                        warnings.append(f"Attempt {attempt + 1} failed: {parse_err}")
                        messages.append({"role": "assistant", "content": resp.content})
                        messages.append({
                            "role": "user",
                            "content": (
                                f"Erreur : {parse_err}\n\n"
                                "Réponds avec EXACTEMENT deux blocs fenced : "
                                "```html ... ``` contenant le HTML complet, puis "
                                "```json ... ``` contenant uniquement {\"path\": \"...\", \"sections\": [...]}. "
                                "Ne mets JAMAIS le HTML à l'intérieur du JSON."
                            ),
                        })
                        continue
                    raise parse_err

            except (LLMError, ValueError, KeyError) as e:
                last_error = e
                if attempt == max_retries:
                    break

        import logging
        log = logging.getLogger(__name__)
        log.warning("agent %s used fallback after failing all attempts. Last error: %s", self.name, last_error)
        fb = self.fallback(inp, str(last_error))
        return AgentOutput(
            agent=self.name,
            status="partial",
            data=fb,
            tokens=TokenUsage(prompt=tokens_prompt, completion=tokens_completion),
            duration_ms=int((time.perf_counter() - t0) * 1000),
            warnings=warnings + [f"fallback used: {last_error}"],
        )

    def _parse_dual_block(self, text: str, inp: AgentInput) -> dict[str, Any]:
        page = inp.params.get("page", {})

        # Extract HTML block
        html_match = _HTML_FENCE_RE.search(text)
        if not html_match:
            # Fallback: try to find raw <!doctype html> in the response
            doc_start = text.lower().find("<!doctype html")
            if doc_start == -1:
                raise ValueError("static_page_builder: no ```html block found")
            html = text[doc_start:].strip()
        else:
            html = html_match.group(1).strip()

        if "<!doctype html" not in html.lower():
            raise ValueError("static_page_builder: html block missing <!doctype html>")

        # Extract JSON metadata block
        sections: list[dict[str, Any]] = []
        path = str(page.get("path") or "index.html").strip().lstrip("/")

        json_match = _JSON_FENCE_RE.search(text)
        if json_match:
            try:
                meta = json.loads(json_match.group(1).strip())
                if isinstance(meta, dict):
                    path = str(meta.get("path") or path).strip().lstrip("/")
                    if isinstance(meta.get("sections"), list):
                        sections = meta["sections"]
            except json.JSONDecodeError:
                pass  # metadata block is optional

        # Inject required assets if missing
        if "cdn.tailwindcss.com" not in html:
            html = html.replace("</head>", '  <script src="https://cdn.tailwindcss.com"></script>\n</head>')
        if "styles.css" not in html:
            html = html.replace("</head>", '  <link rel="stylesheet" href="./styles.css">\n</head>')
        if "script.js" not in html:
            html = html.replace("</head>", '  <script src="./script.js" defer></script>\n</head>')

        return {"path": path, "html": html, "sections": sections}

    def post_process(self, parsed: Any, inp: AgentInput) -> dict[str, Any]:
        # Not called in the custom run() — kept for BaseAgent contract
        return parsed if isinstance(parsed, dict) else {}

    def fallback(self, inp: AgentInput, error: str) -> dict[str, Any]:
        brief = inp.context.get("brief", {})
        plan = inp.context.get("site_planner", {})
        designer = inp.context.get("designer", {})
        page = inp.params.get("page", {})
        business = brief.get("business_name") or brief.get("name") or "Votre marque"
        title = page.get("title") or business
        path = page.get("path") or "index.html"
        tagline = brief.get("tagline") or brief.get("description") or "L'excellence sur-mesure."
        sector = brief.get("sector") or "votre secteur"
        audience = brief.get("target_audience") or "nos clients"
        nav = plan.get("navigation") or [
            {"label": "Accueil", "href": "index.html"},
            {"label": "Services", "href": "services.html"},
            {"label": "Contact", "href": "contact.html"},
        ]
        palette = (designer.get("palette") or {}) if isinstance(designer, dict) else {}
        typo = (designer.get("typography") or {}) if isinstance(designer, dict) else {}
        primary = palette.get("primary") or brief.get("primary_color") or brief.get("brand", {}).get("primary_color") or "#6366f1"
        secondary = palette.get("secondary") or brief.get("secondary_color") or brief.get("brand", {}).get("secondary_color") or "#1e1b4b"
        font_heading = typo.get("heading") or brief.get("font_style") or brief.get("font_pref") or "Inter"
        logo_url = designer.get("logo_url") or brief.get("logo_url") or brief.get("identity", {}).get("logo_url")

        if logo_url:
            brand_html = f'<img src="{logo_url}" alt="{business}" class="h-10 w-auto">'
        else:
            brand_html = f'<span class="text-xl font-bold" style="color: {primary}">{business}</span>'

        nav_html = "".join(
            f'<a class="text-gray-600 transition font-medium" onmouseover="this.style.color=\'{primary}\'" onmouseout="this.style.color=\'#4b5563\'" href="{item.get("href", "#")}">'
            f'{item.get("label", "Page")}</a>'
            for item in nav if isinstance(item, dict)
        )

        page_seo_desc = page.get("seo_description") or brief.get("description") or business
        sector_key = detect_sector(brief)

        html = build_sector_html(
            sector_key,
            business=business, title=title, tagline=tagline, sector=sector,
            audience=audience, locale=inp.locale, primary=primary, secondary=secondary,
            font_heading=font_heading, brand_html=brand_html, nav_html=nav_html,
            page=page, brief=brief, page_seo_desc=page_seo_desc,
        )

        return {
            "path": path,
            "html": html,
            "sections": [
                {"id": "hero", "component": "HeroSplit", "title": str(title), "content": str(page.get("purpose") or ""), "enabled": True}
            ],
            "notes": [error],
        }
