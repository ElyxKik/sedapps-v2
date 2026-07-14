from __future__ import annotations

import json
import re
from html import unescape
from typing import Any

from app.agents.base import AgentInput, AgentOutput, BaseAgent, TokenUsage
from app.llm.deepseek import LLMError

_HTML_FENCE_RE = re.compile(r"```html\s*([\s\S]*?)```", re.IGNORECASE)
_JSON_FENCE_RE = re.compile(r"```json\s*([\s\S]*?)```", re.IGNORECASE)


def _normalized_identifier(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


class StaticPageBuilderAgent(BaseAgent):
    name = "static_page_builder"
    default_temperature = 0.5
    default_max_tokens = 12000

    def system_prompt(self, inp: AgentInput) -> str:
        return """
Tu es un senior frontend designer spécialisé en pages statiques premium.

Tu génères UNE SEULE PAGE HTML à la fois, jamais tout le site.
Tu DOIS utiliser Tailwind CSS CDN pour toute la mise en page (classes utilitaires directement sur les éléments HTML).

Contraintes HTML :
- Document HTML complet d'exception avec <!doctype html>, head, body.
- Inclure dans le <head> : <script src="https://cdn.tailwindcss.com"></script>, <link rel="stylesheet" href="./styles.css">, <script src="./script.js" defer></script>
- Design sur-mesure pour la marque, l'audience et l'objectif du brief. Aucune section générique.
- Header sticky et Footer cohérents avec la navigation globale du site.
- Icônes SVG inline professionnelles pour un rendu ultra-premium.
- Jamais d'emoji sauf demande explicite dans le brief.
- Pas de lorem ipsum, pas de placeholder, pas de TODO. Contenu entièrement rédigé, persuasif, adapté au secteur.
- Chaque page marketing doit contenir au moins 3 sections substantielles, 180 mots utiles et 2 images pertinentes avec alt descriptif.
- Une page de contact doit contenir au moins 1 image, des coordonnées et un formulaire réellement complet.
- Utilise des URLs d'images HTTPS stables (Unsplash source avec paramètres explicites autorisé). N'invente jamais un fichier local absent.
- Respecte toutes les sections demandées dans le brief. Ne fusionne ou ne supprime aucune section activée.
- Si brief.premium == true : esthétique maximale, micro-détails, storytelling immersif.

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
            "Génère cette page en DEUX blocs séparés : ```html ... ``` puis ```json ... ```. "
            "Le JSON doit recenser TOUTES les sections réellement présentes dans le HTML. "
            "Avant de répondre, vérifie le nombre de sections, d'images, la richesse du texte et la conformité au brief."
        )
        return "\n".join(parts)

    async def run(self, inp: AgentInput) -> AgentOutput:  # type: ignore[override]
        import time
        t0 = time.perf_counter()
        warnings: list[str] = []
        max_retries = 2
        messages = [
            {"role": "system", "content": self.composed_system_prompt(inp)},
            {"role": "user", "content": self.user_prompt(inp)},
        ]
        tokens_prompt = tokens_completion = 0
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                resp = await self.client.chat(
                    messages=messages,
                    temperature=self.default_temperature,
                    max_tokens=self.default_max_tokens,
                    thinking=False,
                    response_format_json=False,  # plain text — HTML can't go in JSON mode
                )
                tokens_prompt += resp.usage.prompt_tokens
                tokens_completion += resp.usage.completion_tokens

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

        lower_html = html.lower()
        if "<!doctype html" not in lower_html:
            raise ValueError("static_page_builder: html block missing <!doctype html>")
        if "</html>" not in lower_html or "</body>" not in lower_html:
            raise ValueError("static_page_builder: truncated or incomplete HTML")

        # Extract JSON metadata block
        sections: list[dict[str, Any]] = []
        path = str(page.get("path") or "index.html").strip().lstrip("/")

        json_match = _JSON_FENCE_RE.search(text)
        if not json_match:
            raise ValueError("static_page_builder: required JSON metadata block missing")
        try:
            meta = json.loads(json_match.group(1).strip())
        except json.JSONDecodeError as exc:
            raise ValueError("static_page_builder: invalid JSON metadata") from exc
        if not isinstance(meta, dict) or not isinstance(meta.get("sections"), list):
            raise ValueError("static_page_builder: metadata sections missing")
        path = str(meta.get("path") or path).strip().lstrip("/")
        sections = meta["sections"]

        planned_sections = page.get("sections") if isinstance(page.get("sections"), list) else []
        planned_components = [
            item for item in (page.get("components") or [])
            if str(item).lower() not in {"header", "footer"}
        ]
        enabled_onboarding = [
            item for item in (inp.context.get("brief", {}).get("sections") or [])
            if isinstance(item, dict) and item.get("enabled", True)
        ]
        expected = len(planned_sections) or len(planned_components)
        if path == "index.html" and inp.context.get("brief", {}).get("stack") == "onepage":
            expected = max(expected, len(enabled_onboarding))
        minimum_sections = max(3, expected)
        html_section_count = len(re.findall(r"<section\b", html, re.IGNORECASE))
        if html_section_count < minimum_sections or len(sections) < minimum_sections:
            raise ValueError(
                f"static_page_builder: incomplete sections ({html_section_count} HTML / {len(sections)} metadata, expected {minimum_sections})"
            )

        if path == "index.html" and inp.context.get("brief", {}).get("stack") == "onepage":
            metadata_identifiers = {
                _normalized_identifier(section.get(key))
                for section in sections
                if isinstance(section, dict)
                for key in ("id", "component")
                if section.get(key)
            }
            missing_section_types = []
            for item in enabled_onboarding:
                requested_type = _normalized_identifier(item.get("type"))
                if requested_type and not any(
                    requested_type in identifier or identifier in requested_type
                    for identifier in metadata_identifiers
                ):
                    missing_section_types.append(str(item.get("type")))
            if missing_section_types:
                raise ValueError(
                    "static_page_builder: onboarding section types missing ("
                    + ", ".join(missing_section_types)
                    + ")"
                )

            searchable_html = unescape(
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            ).lower()
            missing_section_values = []
            for item in enabled_onboarding:
                data = item.get("data") if isinstance(item.get("data"), dict) else {}
                for key in ("headline", "title", "description", "body", "cta_text"):
                    value = data.get(key)
                    if isinstance(value, str) and len(value.strip()) >= 3 and value.strip().lower() not in searchable_html:
                        missing_section_values.append(value.strip())
            if missing_section_values:
                raise ValueError(
                    "static_page_builder: onboarding content missing ("
                    + ", ".join(missing_section_values[:3])
                    + ")"
                )
        minimum_images = 1 if "contact" in path else 2
        image_count = len(re.findall(r"<img\b", html, re.IGNORECASE))
        if image_count < minimum_images:
            raise ValueError(
                f"static_page_builder: insufficient images ({image_count}, expected {minimum_images})"
            )
        images_without_alt = len(
            re.findall(r"<img(?![^>]*\balt\s*=)[^>]*>", html, re.IGNORECASE)
        )
        if images_without_alt:
            raise ValueError(
                f"static_page_builder: images without alt text ({images_without_alt})"
            )
        text_only = re.sub(
            r"<script[\s\S]*?</script>|<style[\s\S]*?</style>",
            " ",
            html,
            flags=re.IGNORECASE,
        )
        text_only = unescape(re.sub(r"<[^>]+>", " ", text_only))
        word_count = len(re.findall(r"\b\w{2,}\b", text_only, re.UNICODE))
        minimum_words = 100 if "contact" in path else 180
        if word_count < minimum_words:
            raise ValueError(
                f"static_page_builder: content too thin ({word_count} words, expected {minimum_words})"
            )

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
        page = inp.params.get("page", {})
        business = brief.get("business_name") or brief.get("name") or "Votre marque"
        title = page.get("title") or business
        path = page.get("path") or "index.html"
        tagline = brief.get("tagline") or brief.get("description") or "L'excellence sur-mesure."
        sector = brief.get("sector") or "votre secteur"
        nav = plan.get("navigation") or [
            {"label": "Accueil", "href": "index.html"},
            {"label": "Services", "href": "services.html"},
            {"label": "Contact", "href": "contact.html"},
        ]
        nav_html = "".join(
            f'<a class="text-gray-600 hover:text-indigo-600 transition font-medium" href="{item.get("href", "#")}">'
            f'{item.get("label", "Page")}</a>'
            for item in nav if isinstance(item, dict)
        )
        # SVG inline professionnels (remplacent les emojis interdits)
        svg_bolt = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
        svg_target = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>'
        svg_star = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
        html = f"""<!doctype html>
<html lang="{inp.locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — {business}</title>
  <meta name="description" content="{page.get('seo_description') or brief.get('description') or business}">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="./styles.css">
  <script src="./script.js" defer></script>
</head>
<body class="bg-gray-50 text-gray-900 font-sans">
  <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-4 flex justify-between items-center max-w-7xl mx-auto rounded-full mt-4">
    <a class="text-xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent" href="index.html">{business}</a>
    <nav class="flex gap-6 items-center">{nav_html}</nav>
  </header>
  <main class="max-w-7xl mx-auto px-6 py-12">
    <section class="py-20 text-center flex flex-col items-center">
      <span class="text-sm font-bold tracking-wider uppercase text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">{page.get('purpose') or sector or 'Premium'}</span>
      <h1 class="text-5xl md:text-6xl font-extrabold tracking-tight mt-6 max-w-4xl">{title}</h1>
      <p class="text-lg text-gray-600 mt-6 max-w-2xl leading-relaxed">{brief.get('description') or brief.get('brief') or tagline}</p>
      <div class="mt-10 flex gap-4">
        <a class="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-full shadow-lg hover:shadow-xl transition" href="contact.html">Démarrer le projet</a>
        <a class="px-8 py-3 bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 font-semibold rounded-full transition" href="#features">En savoir plus</a>
      </div>
    </section>
    <section id="features" class="grid grid-cols-1 md:grid-cols-3 gap-8 py-20">
      <article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition">
        <div class="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">{svg_bolt}</div>
        <h2 class="text-xl font-bold mt-6">Design Unique</h2>
        <p class="text-gray-600 mt-2">Une mise en page entièrement personnalisée et optimisée pour votre marque.</p>
      </article>
      <article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition">
        <div class="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">{svg_target}</div>
        <h2 class="text-xl font-bold mt-6">Conversion Maximale</h2>
        <p class="text-gray-600 mt-2">Chaque élément est structuré pour capter l'intérêt et inciter à l'action.</p>
      </article>
      <article class="bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl transition">
        <div class="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">{svg_star}</div>
        <h2 class="text-xl font-bold mt-6">Rendu Premium</h2>
        <p class="text-gray-600 mt-2">Spécifiquement conçu pour mettre en valeur votre expertise en {sector}.</p>
      </article>
    </section>
  </main>
  <footer class="border-t border-gray-100 py-8 text-center text-gray-500 text-sm">&copy; {business} — Tous droits réservés.</footer>
</body>
</html>"""
        return {
            "path": path,
            "html": html,
            "sections": [
                {"id": "hero", "component": "HeroSplit", "title": str(title), "content": str(page.get("purpose") or ""), "enabled": True}
            ],
            "notes": [error],
        }
