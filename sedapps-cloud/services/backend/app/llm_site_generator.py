from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Callable

import httpx

from app.config import settings

ProgressCallback = Callable[[dict[str, Any]], None]


# ===== Orchestration Prompt for Premium Professional Site Generation =====

ORCHESTRATION_SYSTEM_PROMPT = """Tu es le Chef d'Orchestre IA de SedApps, responsable de la création de sites web professionnels et premium.

## Rôle
Coordonner une équipe de 6 agents spécialisés pour transformer un brief client en site web complet, moderne et optimisé.

## Agents sous ta direction
1. **Designer** → Crée la palette de couleurs, la structure de layout, les tokens de design
2. **Copywriter** → Rédige le hero, les CTA, les propositions de valeur, FAQ
3. **Rédacteur** → Développe les sections complètes (about, services, témoignages, blog)
4. **SEO Specialist** → Optimise meta tags, keywords, structure JSON-LD, Open Graph
5. **Frontend Developer** → Produit HTML/CSS/JS responsive et performant
6. **Éditeur** → Revue qualité, corrections, cohérence globale

## Processus de création

### Phase 1: Analyse du brief
- Extraire les objectifs métier, la cible, le ton, les offres
- Identifier les pages et sections prioritaires
- Déterminer la stratégie de design (moderne, minimaliste, premium, etc.)

### Phase 2: Design & Architecture
- Designer crée les tokens (couleurs, typographie, spacing, radius)
- Définir la structure de layout (header, hero, sections, footer)
- Établir les guidelines de cohérence visuelle

### Phase 3: Contenu & Rédaction
- Copywriter crée le hero et les CTA
- Rédacteur développe les sections détaillées
- Assurer la cohérence du ton et du message

### Phase 4: SEO & Optimisation
- SEO Specialist optimise pour les moteurs de recherche
- Ajouter meta tags, keywords, structured data
- Préparer Open Graph pour les réseaux sociaux

### Phase 5: Développement Frontend
- Frontend Developer produit HTML/CSS/JS
- Assurer la responsivité (mobile, tablet, desktop)
- Optimiser les performances (Lighthouse 90+)

### Phase 6: Revue & Finalisation
- Éditeur revoit la qualité globale
- Corrections finales et cohérence
- Validation avant publication

## Qualité Premium
- Design moderne et professionnel
- Contenu persuasif et bien structuré
- Performance optimale (Core Web Vitals)
- Accessibilité WCAG AA
- SEO-friendly et prêt pour la conversion
- Code clean et maintenable

## Output attendu
Chaque agent produit un JSON structuré avec ses résultats spécifiques.
L'Éditeur produit le HTML/CSS/JS final et un rapport de qualité."""


# ===== Fallback (used when no DeepSeek key configured) =====

def fallback_site_payload(brief: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    business = brief.get("business_name") or brief.get("name") or "Mon Site"
    sector = brief.get("sector") or "Services"
    description = brief.get("brief") or brief.get("description") or f"Site moderne pour {business}"
    primary = brief.get("primary_color") or "#0EA5E9"
    secondary = brief.get("secondary_color") or "#38BDF8"
    font = brief.get("font_style") or "Inter"
    tagline = brief.get("tagline") or f"{business}, votre présence web professionnelle"

    design_tokens = {"primary": primary, "secondary": secondary, "background": "#F8FAFC", "font_heading": font}
    sections = [
        {"id": "hero", "title": "Accueil", "content": tagline, "enabled": True},
        {"id": "services", "title": "Services", "content": f"Des solutions adaptées au secteur {sector}.", "enabled": True},
        {"id": "about", "title": "À propos", "content": description, "enabled": True},
        {"id": "contact", "title": "Contact", "content": "Contactez-nous pour démarrer votre projet.", "enabled": True},
    ]
    files = [
        {"path": "index.html", "content": _fallback_html(business, sector, description, tagline, design_tokens)},
        {"path": "styles.css", "content": _fallback_css(design_tokens)},
        {"path": "script.js", "content": "document.querySelector('form')?.addEventListener('submit', e => e.preventDefault());"},
    ]
    output = {
        "site_schema": {"pages": 1, "sections": len(sections), "sections_data": sections},
        "design_tokens": design_tokens,
        "seo": {"title": f"{business} | {sector}", "description": description[:155]},
        "generated_files": files,
    }
    agents = _mock_agents(brief, design_tokens, sections, files)
    return agents, output, sections, files


def _fallback_html(business: str, sector: str, description: str, tagline: str, tokens: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{business} | {sector}</title>
  <meta name=\"description\" content=\"{description[:155]}\" />
  <link rel=\"stylesheet\" href=\"./styles.css\" />
</head>
<body>
  <header><h1>{business}</h1><p>{tagline}</p></header>
  <main>
    <section><h2>Services</h2><p>Des solutions adaptées au secteur {sector}.</p></section>
    <section id=\"contact\"><h2>Contact</h2><form><input placeholder=\"Email\" /><textarea placeholder=\"Message\"></textarea><button>Envoyer</button></form></section>
  </main>
  <script src=\"./script.js\"></script>
</body>
</html>"""


def _fallback_css(tokens: dict[str, Any]) -> str:
    primary = tokens.get("primary", "#0EA5E9")
    bg = tokens.get("background", "#F8FAFC")
    font = tokens.get("font_heading", "Inter")
    return f""":root {{ --primary: {primary}; --bg: {bg}; }}
body {{ margin: 0; font-family: {font}, system-ui, sans-serif; background: var(--bg); color: #0f172a; }}
header {{ padding: 96px 32px; background: var(--primary); color: white; }}
main {{ max-width: 1120px; margin: auto; padding: 48px 20px; }}
button {{ background: #0f172a; color: white; border: 0; border-radius: 999px; padding: 12px 18px; }}
input, textarea {{ display: block; width: 100%; margin: 12px 0; padding: 14px; border: 1px solid #cbd5e1; border-radius: 14px; }}"""


def _mock_agents(brief: dict[str, Any], tokens: dict[str, Any], sections: list[dict[str, Any]], files: list[dict[str, str]]) -> list[dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    return [
        {"id": "agent-designer", "name": "designer", "status": "ok", "model": "fallback", "duration_ms": 600, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": tokens, "created_at": now, "warnings": []},
        {"id": "agent-copywriter", "name": "copywriter", "status": "ok", "model": "fallback", "duration_ms": 600, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": {"hero": sections[0]["content"]}, "created_at": now, "warnings": []},
        {"id": "agent-redacteur", "name": "redacteur", "status": "ok", "model": "fallback", "duration_ms": 600, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": {"sections": sections}, "created_at": now, "warnings": []},
        {"id": "agent-seo", "name": "seo_specialist", "status": "ok", "model": "fallback", "duration_ms": 600, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": {"title": brief.get("business_name", "")}, "created_at": now, "warnings": []},
        {"id": "agent-frontend", "name": "frontend_developer", "status": "ok", "model": "fallback", "duration_ms": 800, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": {"files": [file["path"] for file in files]}, "created_at": now, "warnings": []},
        {"id": "agent-editeur", "name": "editeur", "status": "ok", "model": "fallback", "duration_ms": 400, "tokens_in": 0, "tokens_out": 0, "input": brief, "output": {"reviewed": True}, "created_at": now, "warnings": []},
    ]


# ===== DeepSeek client =====

def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
    decoder = json.JSONDecoder()
    best: dict[str, Any] | None = None
    idx = 0
    while True:
        start = content.find("{", idx)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            idx = start + 1
            continue
        if isinstance(obj, dict) and ("files" in obj or "design_tokens" in obj or "sections" in obj):
            return obj
        if best is None and isinstance(obj, dict):
            best = obj
        idx = end
    if best is not None:
        return best
    raise ValueError(f"DeepSeek response is not valid JSON: {content[:200]}")


def _deepseek_try(model: str, system_prompt: str, user_payload: dict[str, Any], timeout: int) -> tuple[dict[str, Any], dict[str, int], int]:
    started = time.time()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
        "max_tokens": 8000,
    }
    response = httpx.post(
        f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    usage = data.get("usage") or {}
    message = data["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning_content") or ""
    if not content.strip():
        raise RuntimeError("DeepSeek a renvoyé un contenu vide.")
    duration_ms = int((time.time() - started) * 1000)
    return _extract_json(content), {"tokens_in": usage.get("prompt_tokens", 0), "tokens_out": usage.get("completion_tokens", 0)}, duration_ms


def _deepseek_call(system_prompt: str, user_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int], int]:
    primary = settings.deepseek_model
    fallback = "deepseek-v4-flash" if primary != "deepseek-v4-flash" else None
    primary_timeout = 300 if primary == "deepseek-v4-pro" else 120
    try:
        return _deepseek_try(primary, system_prompt, user_payload, timeout=primary_timeout)
    except Exception as exc:
        if fallback is None:
            raise
        # Auto-fallback rapide si le modèle principal échoue (timeout, JSON cassé, etc.)
        return _deepseek_try(fallback, system_prompt, user_payload, timeout=120)


def _agent_call(agent_id: str, name: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        output, usage, duration_ms = _deepseek_call(system_prompt, payload)
        status = "ok"
        warnings: list[str] = []
        error: str | None = None
    except Exception as exc:
        output, usage, duration_ms = {}, {"tokens_in": 0, "tokens_out": 0}, 0
        status = "failed"
        warnings = [str(exc)]
        error = str(exc)
    return {
        "id": agent_id,
        "name": name,
        "status": status,
        "model": settings.deepseek_model,
        "prompt_version": 1,
        "duration_ms": duration_ms,
        "tokens_in": usage["tokens_in"],
        "tokens_out": usage["tokens_out"],
        "input": payload,
        "output": output,
        "warnings": warnings,
        "error": error,
        "created_at": datetime.utcnow().isoformat(),
    }


# ===== Agent prompts (7-agent pipeline) =====

_ORCHESTRATOR_PROMPT = """You are the Site Director of an AI web agency.

Your role is to transform a user request into a complete execution plan for a static website (HTML, CSS, JavaScript only).

You do NOT design visuals or code. You only plan.

You must:
- Identify the website type (landing page, portfolio, business site, SaaS, etc.)
- Extract business goal and target audience
- Define required pages (usually single-page or few pages)
- Define required sections per page
- Define technical constraints (no backend, no frameworks unless explicitly required)
- Define overall style direction (modern, luxury, minimal, bold, corporate, etc.)

Output must be strict JSON:

{
  "project_type": "",
  "goal": "",
  "target_audience": "",
  "pages": [],
  "sections_per_page": {},
  "style_direction": "",
  "functional_requirements": [],
  "technical_constraints": ["HTML", "CSS", "Vanilla JS only"],
  "priority_features": []
}

Be precise, structured, and production-oriented. Avoid vague descriptions."""

_UX_ARCHITECT_PROMPT = """You are a senior UX Architect specialized in static websites.

Your job is to design the INFORMATION ARCHITECTURE only.

You receive a project plan and must convert it into:
- page structure
- section hierarchy
- content flow logic
- user journey

You DO NOT design visuals, colors, or code. You think in HTML sections.

Output STRICT JSON:

{
  "pages": {
    "home": {
      "user_flow": [],
      "sections": [
        "header",
        "hero",
        "social_proof",
        "features",
        "about",
        "cta",
        "footer"
      ]
    }
  }
}

Rules:
- Prioritize conversion-driven structure
- Always include CTA logic
- Ensure logical storytelling flow
- Optimize for marketing effectiveness"""

_DESIGN_SYSTEM_PROMPT = """You are a senior UI Designer specialized in modern web design systems.

Your role is to define a complete DESIGN SYSTEM for a static website.

You must NOT create layouts or content. You only define visual rules.

Output STRICT JSON:

{
  "color_palette": {
    "primary": "",
    "secondary": "",
    "background": "",
    "text": "",
    "accent": ""
  },
  "typography": {
    "font_primary": "",
    "font_secondary": "",
    "scale": {
      "h1": "",
      "h2": "",
      "body": ""
    }
  },
  "spacing_system": "8px grid",
  "border_radius": "",
  "shadows": "",
  "ui_style": "",
  "component_styles": {
    "button": "",
    "card": "",
    "input": ""
  },
  "design_principles": []
}

Rules:
- Ensure high-end modern aesthetic
- Maintain consistency and scalability
- Optimize for readability and conversion
- Avoid overly complex design systems
- All colors must be valid CSS hex values"""

_COPYWRITER_PROMPT = """You are a senior conversion copywriter for high-end web agencies.

Your job is to write all website content.

You receive:
- UX structure
- business goal
- target audience

You must produce persuasive, clear, modern marketing copy.

Rules:
- Write concise, high-impact sentences
- Focus on conversion and clarity
- Avoid generic AI wording
- Adapt tone to brand style
- Match the language requested in the brief (default: French if the brief is in French)

Output STRICT JSON:

{
  "global_tone": "",
  "sections": {
    "hero": {
      "title": "",
      "subtitle": "",
      "cta_primary": "",
      "cta_secondary": ""
    },
    "features": [],
    "about": "",
    "testimonials": [],
    "cta_final": ""
  }
}

Rules:
- Every sentence must serve conversion or clarity
- No filler text
- No repetition"""

_FRONTEND_BUILDER_PROMPT = """You are a senior Frontend Engineer specialized in static websites.

You must generate production-ready code using ONLY:
- HTML5
- CSS3
- Vanilla JavaScript (if needed)

No frameworks allowed.

You receive:
- UX structure
- Design system (color_palette, typography, spacing_system, etc.)
- Copywriting content

You must output three files:
1. index.html
2. styles.css   (NOTE: filename is `styles.css` with an `s`, not `style.css`)
3. script.js    (optional but recommended)

Rules:
- Clean semantic HTML5 with lang attribute matching the copy language
- index.html MUST link `./styles.css` in <head> and load `./script.js` with `defer` before </body>
- Mobile-first responsive design
- Pixel-perfect implementation of design system (use CSS custom properties from color_palette/typography)
- Reusable CSS classes
- Performance optimized
- Accessibility best practices (ARIA, semantic tags, alt text, focus-visible)
- No external dependencies unless explicitly required (Google Fonts allowed via <link>)
- Section IDs must match the UX architecture; nav anchors must point to existing IDs
- Include meta description, viewport, og:title, og:description and JSON-LD Organization in <head>

IMPORTANT:
- Follow spacing system strictly
- Follow typography scale strictly
- Ensure perfect visual hierarchy
- No Lorem Ipsum, no TODO, no placeholder content

Output format (STRICT JSON, no markdown):

{
  "index.html": "<!doctype html>...",
  "styles.css": ":root {...} ...",
  "script.js": "..."
}"""

_QA_PROMPT = """You are a senior QA Engineer + UX Reviewer for web interfaces.

Your job is to critically analyze a generated website (HTML, CSS, JS provided as input).

You must:
- Detect UX issues
- Detect UI inconsistencies
- Detect responsiveness problems
- Detect accessibility issues
- Detect performance issues
- Simulate real user behavior

You are STRICT and uncompromising.

Output STRICT JSON:

{
  "critical_issues": [],
  "ui_issues": [],
  "ux_issues": [],
  "responsive_issues": [],
  "accessibility_issues": [],
  "performance_notes": [],
  "recommended_fixes": [],
  "overall_score": 0
}

Rules:
- Do NOT be lenient
- Think like a senior Google-level reviewer
- Prioritize conversion + usability
- Always propose fixes, not just problems
- overall_score is an integer between 0 and 100"""

_REFINEMENT_PROMPT = """You are a senior web refinement engineer.

You receive QA feedback and must improve the website accordingly.

Rules:
- Fix all critical issues first
- Preserve design system consistency
- Do not break existing structure
- Improve UX subtly, not radically
- Keep filenames identical: `index.html`, `styles.css`, `script.js`

Output STRICT JSON with the updated full files (return only the files you modified):

{
  "summary": "what was changed and why",
  "fixes_applied": ["short description of each fix"],
  "files": {
    "index.html": "<!doctype html>...",
    "styles.css": ":root {...}",
    "script.js": "..."
  }
}"""


# ===== Pipeline =====

def generate_llm_site_payload(
    brief: dict[str, Any],
    on_progress: ProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    def _emit(step: str, status: str, progress: int, label: str, **extra: Any) -> None:
        if on_progress is None:
            return
        event = {"step": step, "status": status, "progress": progress, "label": label, "ts": datetime.utcnow().isoformat()}
        event.update(extra)
        try:
            on_progress(event)
        except Exception:
            pass

    if not settings.deepseek_api_key:
        _emit("fallback", "running", 30, "Mode local (sans clé DeepSeek)")
        agents_fb, output_fb, sections_fb, files_fb = fallback_site_payload(brief)
        _emit("done", "ok", 100, "Site généré (fallback)", files=len(files_fb))
        return agents_fb, output_fb, sections_fb, files_fb

    agents: list[dict[str, Any]] = []

    # 1. Orchestrateur — Site Director
    _emit("orchestrate", "running", 3, "Orchestrateur : analyse du brief et plan de site")
    orchestrator = _agent_call("agent-orchestrator", "orchestrator", _ORCHESTRATOR_PROMPT, {"brief": brief})
    agents.append(orchestrator)
    _emit("orchestrate", orchestrator["status"], 12, f"Orchestrateur terminé ({orchestrator['status']})", agent="orchestrator")
    plan = orchestrator["output"] if orchestrator["status"] == "ok" else {
        "project_type": "landing page",
        "goal": brief.get("brief") or brief.get("business_name") or "site vitrine",
        "target_audience": brief.get("audience") or "grand public",
        "pages": ["home"],
        "sections_per_page": {"home": ["hero", "features", "about", "contact"]},
        "style_direction": brief.get("style") or "modern, professional",
        "functional_requirements": [],
        "technical_constraints": ["HTML", "CSS", "Vanilla JS only"],
        "priority_features": [],
    }

    # 2. UX Architect — DOM structure
    _emit("ux", "running", 18, "UX Architect : architecture de l'information")
    ux = _agent_call("agent-ux-architect", "ux_architect", _UX_ARCHITECT_PROMPT, {"brief": brief, "plan": plan})
    agents.append(ux)
    _emit("ux", ux["status"], 26, f"UX Architect terminé ({ux['status']})", agent="ux_architect")
    architecture = ux["output"] if ux["status"] == "ok" else {
        "pages": {
            "home": {
                "user_flow": ["land", "engage", "convert"],
                "sections": ["header"] + (plan.get("sections_per_page", {}).get("home") or ["hero", "features", "about", "contact"]) + ["footer"],
            }
        }
    }

    # 3. UI / Design System
    _emit("design", "running", 32, "Design System : charte visuelle")
    designer = _agent_call("agent-design-system", "design_system", _DESIGN_SYSTEM_PROMPT, {"brief": brief, "plan": plan})
    agents.append(designer)
    _emit("design", designer["status"], 42, f"Design System terminé ({designer['status']})", agent="design_system")
    design_system = designer["output"] if designer["status"] == "ok" else {}
    design_tokens = _design_system_to_tokens(design_system, brief)

    # 4. Copywriter
    _emit("copy", "running", 50, "Copywriter : rédaction de tous les textes")
    copywriter = _agent_call(
        "agent-copywriter",
        "copywriter",
        _COPYWRITER_PROMPT,
        {"brief": brief, "plan": plan, "architecture": architecture},
    )
    agents.append(copywriter)
    _emit("copy", copywriter["status"], 60, f"Copywriter terminé ({copywriter['status']})", agent="copywriter")
    copy = copywriter["output"] if copywriter["status"] == "ok" else {}
    sections = _copy_to_sections(copy, plan, architecture)

    # 5. Frontend Builder — combine tout
    _emit("frontend", "running", 66, "Frontend Builder : génération HTML / CSS / JS")
    frontend = _agent_call(
        "agent-frontend-builder",
        "frontend_builder",
        _FRONTEND_BUILDER_PROMPT,
        {
            "brief": brief,
            "plan": plan,
            "architecture": architecture,
            "design_system": design_system,
            "design_tokens": design_tokens,
            "copy": copy,
        },
    )
    agents.append(frontend)
    _emit("frontend", frontend["status"], 80, f"Frontend Builder terminé ({frontend['status']})", agent="frontend_builder")
    files = _normalize_files(frontend["output"]) if frontend["status"] == "ok" else []
    if not files:
        business = brief.get("business_name") or "Mon Site"
        sector = brief.get("sector") or "Services"
        description = brief.get("brief") or ""
        hero_block = (copy.get("sections") or {}).get("hero") if isinstance(copy.get("sections"), dict) else None
        tagline = (hero_block or {}).get("title") if isinstance(hero_block, dict) else None
        tagline = tagline or business
        files = [
            {"path": "index.html", "content": _fallback_html(business, sector, description, tagline, design_tokens)},
            {"path": "styles.css", "content": _fallback_css(design_tokens)},
            {"path": "script.js", "content": "document.querySelector('form')?.addEventListener('submit', e => e.preventDefault());"},
        ]

    # 6. QA / Polish — LLM review
    _emit("qa", "running", 84, "QA / Polish : revue qualité")
    qa_agent = _agent_call(
        "agent-qa",
        "qa_polish",
        _QA_PROMPT,
        {"design_system": design_system, "architecture": architecture, "copy": copy, "files": _files_to_dict(files)},
    )
    agents.append(qa_agent)
    qa_out = qa_agent["output"] if qa_agent["status"] == "ok" else {}
    qa_llm_score = qa_out.get("overall_score") if isinstance(qa_out, dict) else None
    critical = qa_out.get("critical_issues") or [] if isinstance(qa_out, dict) else []
    _emit("qa", qa_agent["status"], 88, f"QA terminé ({qa_agent['status']}) — score {qa_llm_score}", agent="qa_polish", critical=len(critical))

    # 7. Refinement — conditionnel : si critical issues OU score < 75
    refinement_done = False
    needs_refinement = bool(critical) or (isinstance(qa_llm_score, (int, float)) and qa_llm_score < 75)
    if needs_refinement and qa_agent["status"] == "ok":
        _emit("refine", "running", 90, "Refinement : application des corrections QA")
        refinement = _agent_call(
            "agent-refinement",
            "refinement",
            _REFINEMENT_PROMPT,
            {"qa_feedback": qa_out, "files": _files_to_dict(files), "design_system": design_system},
        )
        agents.append(refinement)
        if refinement["status"] == "ok":
            refined_files = _normalize_files(refinement["output"])
            for rf in refined_files:
                replaced = False
                for index, existing in enumerate(files):
                    if existing.get("path") == rf.get("path"):
                        files[index] = rf
                        replaced = True
                        break
                if not replaced:
                    files.append(rf)
            refinement_done = True
            _emit("refine", "ok", 94, f"Refinement terminé : {len(refined_files)} fichiers mis à jour", agent="refinement")
        else:
            _emit("refine", "failed", 94, f"Refinement échoué : {refinement.get('error')}", agent="refinement")
    else:
        _emit("refine", "skipped", 94, "Refinement non nécessaire (score OK)")

    # QA déterministe (post-LLM) — répare ce qui peut l'être en local
    _emit("validate", "running", 96, "Validation déterministe finale")
    qa_report = _validate_generated_files(files, sections)
    qa_report["llm_score"] = qa_llm_score
    qa_report["llm_critical_issues"] = critical
    qa_report["llm_recommended_fixes"] = qa_out.get("recommended_fixes") if isinstance(qa_out, dict) else []
    qa_report["refinement_applied"] = refinement_done
    if qa_report["fixes_applied"]:
        _emit("validate", "ok", 98, f"Validation : {len(qa_report['fixes_applied'])} corrections auto", warnings=qa_report["warnings"])
    elif qa_report["warnings"]:
        _emit("validate", "ok", 98, "Validation : avertissements présents", warnings=qa_report["warnings"])
    else:
        _emit("validate", "ok", 98, "Validation : OK")

    output = {
        "site_schema": {"pages": len(plan.get("pages", ["home"])), "sections": len(sections), "sections_data": sections},
        "plan": plan,
        "architecture": architecture,
        "design_system": design_system,
        "design_tokens": design_tokens,
        "copy": copy,
        "qa": qa_report,
        "generated_files": files,
    }
    _emit("done", "ok", 100, "Site généré", files=len(files), score=qa_llm_score, refined=refinement_done)
    return agents, output, sections, files


# ===== Format adapters =====

def _design_system_to_tokens(ds: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    """Convert design_system (color_palette/typography) into flat design_tokens used by the rest of the app."""
    palette = ds.get("color_palette") if isinstance(ds, dict) else None
    palette = palette if isinstance(palette, dict) else {}
    typo = ds.get("typography") if isinstance(ds, dict) else None
    typo = typo if isinstance(typo, dict) else {}
    return {
        "primary": palette.get("primary") or brief.get("primary_color") or "#0EA5E9",
        "secondary": palette.get("secondary") or brief.get("secondary_color") or "#38BDF8",
        "accent": palette.get("accent") or "#F59E0B",
        "background": palette.get("background") or "#F8FAFC",
        "surface": palette.get("surface") or "#FFFFFF",
        "text": palette.get("text") or "#0F172A",
        "text_muted": palette.get("text_muted") or "#64748B",
        "border": "#E2E8F0",
        "font_heading": typo.get("font_primary") or brief.get("font_style") or "Inter",
        "font_body": typo.get("font_secondary") or typo.get("font_primary") or brief.get("font_style") or "Inter",
        "radius": (ds.get("border_radius") if isinstance(ds, dict) else None) or "16px",
        "shadow": (ds.get("shadows") if isinstance(ds, dict) else None) or "0 10px 30px rgba(15,23,42,0.12)",
        "ui_style": ds.get("ui_style") if isinstance(ds, dict) else None,
    }


def _copy_to_sections(copy: dict[str, Any], plan: dict[str, Any], architecture: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert copywriter output into the legacy sections list format used by Project.sections."""
    sections_out: list[dict[str, Any]] = []
    sections_data = copy.get("sections") if isinstance(copy.get("sections"), dict) else {}

    # Hero
    hero = sections_data.get("hero") if isinstance(sections_data, dict) else None
    if isinstance(hero, dict):
        title = hero.get("title") or "Bienvenue"
        subtitle = hero.get("subtitle") or ""
        content = subtitle or title
        sections_out.append({"id": "hero", "title": title, "content": content, "enabled": True})

    # Features
    features = sections_data.get("features") if isinstance(sections_data, dict) else None
    if isinstance(features, list) and features:
        feature_text = " · ".join(
            (f.get("title") if isinstance(f, dict) else str(f))
            for f in features
            if f
        )
        sections_out.append({"id": "features", "title": "Fonctionnalités", "content": feature_text, "enabled": True})

    # About
    about = sections_data.get("about") if isinstance(sections_data, dict) else None
    if isinstance(about, str) and about.strip():
        sections_out.append({"id": "about", "title": "À propos", "content": about, "enabled": True})

    # Final CTA
    cta_final = sections_data.get("cta_final") if isinstance(sections_data, dict) else None
    if isinstance(cta_final, str) and cta_final.strip():
        sections_out.append({"id": "cta", "title": "Appel à l'action", "content": cta_final, "enabled": True})

    if sections_out:
        return sections_out

    # Fallback: derive from plan
    home_sections = (plan.get("sections_per_page") or {}).get("home") if isinstance(plan.get("sections_per_page"), dict) else None
    if not home_sections:
        home_sections = (architecture.get("pages") or {}).get("home", {}).get("sections") if isinstance(architecture.get("pages"), dict) else None
    home_sections = home_sections or ["hero", "features", "about", "contact"]
    return [
        {"id": s_id, "title": s_id.replace("_", " ").title(), "content": plan.get("goal", ""), "enabled": True}
        for s_id in home_sections
        if s_id not in ("header", "footer")
    ]


def _normalize_files(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Accept either {"files": [{path, content}, ...]} or {"index.html": "...", "styles.css": "..."} and normalize."""
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("files"), list):
        files = payload["files"]
    elif isinstance(payload.get("files"), dict):
        files = [{"path": k, "content": v} for k, v in payload["files"].items() if isinstance(v, str)]
    else:
        # Direct flat format from new Frontend Builder prompt
        files = []
        for key in ("index.html", "styles.css", "style.css", "script.js"):
            if isinstance(payload.get(key), str):
                # Normalize style.css → styles.css for compatibility with preview server
                norm_key = "styles.css" if key == "style.css" else key
                files.append({"path": norm_key, "content": payload[key]})
    return [
        f for f in files
        if isinstance(f, dict)
        and isinstance(f.get("path"), str)
        and isinstance(f.get("content"), str)
        and f.get("path")
    ]


def _files_to_dict(files: list[dict[str, str]]) -> dict[str, str]:
    """Convert files list back to {filename: content} for prompts."""
    return {f["path"]: f["content"] for f in files if isinstance(f, dict) and f.get("path")}


# ===== QA validation helpers =====

def _validate_generated_files(
    files: list[dict[str, str]],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate generated HTML/CSS/JS and apply minimal fixes."""
    import re

    warnings: list[str] = []
    fixes_applied: list[str] = []

    by_path = {f.get("path"): f for f in files if isinstance(f, dict)}
    html_file = by_path.get("index.html")
    css_file = by_path.get("styles.css")
    js_file = by_path.get("script.js")

    if not html_file or not html_file.get("content"):
        warnings.append("index.html manquant ou vide")
        return {"warnings": warnings, "fixes_applied": fixes_applied, "ok": False}

    html = html_file["content"]

    for needle, msg in [
        ("<html", "balise <html> manquante"),
        ("<head", "balise <head> manquante"),
        ("<body", "balise <body> manquante"),
        ("</html>", "balise </html> de fermeture manquante"),
    ]:
        if needle not in html.lower():
            warnings.append(msg)

    if css_file and "styles.css" not in html:
        html = html.replace("</head>", '  <link rel="stylesheet" href="./styles.css" />\n</head>', 1)
        fixes_applied.append("ajout du <link> styles.css manquant")

    if js_file and "script.js" not in html:
        html = html.replace("</body>", '  <script defer src="./script.js"></script>\n</body>', 1)
        fixes_applied.append("ajout du <script> script.js manquant")

    if "viewport" not in html:
        html = html.replace("</head>", '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n</head>', 1)
        fixes_applied.append("ajout du meta viewport")

    if re.search(r"<html(?![^>]*\blang=)", html, flags=re.IGNORECASE):
        html = re.sub(r"<html", '<html lang="fr"', html, count=1, flags=re.IGNORECASE)
        fixes_applied.append('ajout de lang="fr" sur <html>')

    anchor_targets = set(re.findall(r'href="#([^"\s]+)"', html))
    section_ids = {s.get("id") for s in sections if isinstance(s, dict) and s.get("id")}
    existing_ids = set(re.findall(r'\bid="([^"\s]+)"', html)) | section_ids
    broken = [a for a in anchor_targets if a and a not in existing_ids]
    if broken:
        warnings.append(f"ancres cassées : {', '.join(sorted(broken)[:5])}")

    for placeholder in ("Lorem ipsum", "lorem ipsum", "TODO", "FIXME"):
        if placeholder in html:
            warnings.append(f"contenu placeholder détecté : {placeholder}")
            break

    if fixes_applied:
        html_file["content"] = html

    if css_file and css_file.get("content"):
        css = css_file["content"]
        if css.count("{") != css.count("}"):
            warnings.append("styles.css : accolades non équilibrées")

    return {
        "warnings": warnings,
        "fixes_applied": fixes_applied,
        "ok": not warnings or len(fixes_applied) > 0,
        "anchors_checked": len(anchor_targets),
        "broken_anchors": broken,
    }


# ===== Single-shot pipeline (new) =====

_SINGLE_SHOT_PROMPT = """Tu es l'architecte web senior de SedApps, équivalent d'une équipe d'agence digitale premium composée d'un directeur artistique, d'un designer system, d'un copywriter, d'un développeur front-end senior, d'un expert SEO et d'un QA engineer.

À partir d'un brief client, tu produis un site web ou une application web vitrine professionnelle et premium COMPLÈTE en un seul JSON.

Philosophie de conception inspirée des meilleurs agents SedApps :
- Construis le design system AVANT le code : les couleurs, typographies, espacements, ombres, rayons, effets et animations doivent guider tout le site.
- Pense comme une agence livrant un site à 50k€+ : rien ne doit être générique, chaque section doit être adaptée au secteur, à la marque et à l'objectif business.
- Chaque pixel doit avoir une intention : hiérarchie claire, CTA visibles, profondeur visuelle, responsive mobile-first, micro-interactions.
- Découpe mentalement le projet en étapes : design tokens → structure sémantique → contenu persuasif → interactions → QA accessibilité/performance.
- Avant de répondre, fais une revue interne : liens CSS/JS corrects, ancres cohérentes, balises fermées, contraste lisible, aucune dépendance inutile, aucun contenu placeholder.

Réponds STRICTEMENT en JSON valide, sans markdown, avec cette structure exacte :
{
  "design_tokens": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "surface": "#hex",
    "text": "#hex",
    "text_muted": "#hex",
    "font_heading": "string (nom Google Font)",
    "font_body": "string",
    "radius": "12px",
    "shadow": "0 10px 30px rgba(15,23,42,0.12)",
    "gradient_hero": "linear-gradient(...)",
    "glass_bg": "rgba(...)",
    "animation_ease": "cubic-bezier(...)"
  },
  "seo": {
    "meta_title": "string <= 60 caractères",
    "meta_description": "string <= 155 caractères",
    "keywords": ["..."],
    "og_image_alt": "string"
  },
  "sections": [
    {"id": "hero", "title": "string", "content": "string court", "enabled": true},
    {"id": "services", "title": "...", "content": "...", "enabled": true},
    {"id": "about", "title": "...", "content": "...", "enabled": true},
    {"id": "contact", "title": "...", "content": "...", "enabled": true}
  ],
  "files": [
    {"path": "index.html", "content": "<!doctype html>..."},
    {"path": "styles.css", "content": ":root {...} ..."},
    {"path": "script.js", "content": "..."}
  ]
}

Règles strictes pour index.html :
- HTML5 valide, lang="fr", balises sémantiques (header, nav, main, section, footer)
- Charge styles.css en <link> et script.js en <script defer> (chemins relatifs)
- Inclut meta description, og:title, og:description, og:image et JSON-LD Organization
- Header avec nav links vers les sections (ancres #id)
- Hero premium avec h1 spécifique à la marque, sous-titre orienté bénéfices, 2 CTAs et preuve de confiance
- Sections détaillées avec textes persuasifs, cartes visuelles, bénéfices, preuves, FAQ ou process si pertinent
- Formulaire contact (name, email, message, bouton submit)
- Footer avec copyright, liens légaux
- Aucune dépendance externe sauf Google Fonts (préchargé)
- Accessibilité : aria-label, alt sur images, contraste suffisant
- Ajoute des commentaires de section HTML : <!-- SECTION: hero --> ... <!-- /SECTION: hero -->

Règles strictes pour styles.css :
- Variables CSS depuis design_tokens (--primary, --secondary, --accent, --bg, --surface, --text, --text-muted, --radius, --shadow, etc.)
- Système visuel premium : palette cohérente, typographie expressive, spacing scale, glassmorphism si adapté, ombres et gradients maîtrisés
- Reset minimal, box-sizing border-box
- Responsive mobile-first (media queries 768px et 1024px)
- Animations subtiles au scroll, hover states, focus-visible, transitions fluides
- Pas de framework, CSS pur
- Ajoute des commentaires de section CSS : /* SECTION: hero */ ... /* /SECTION: hero */

Règles strictes pour script.js :
- Vanilla JS, pas de jQuery/framework
- Smooth scroll sur les ancres
- Préventif submit du formulaire avec alerte
- Mobile menu toggle si nécessaire
- Intersection Observer pour révéler les sections au scroll si pertinent
- Code robuste : vérifie l'existence des éléments avant d'attacher les events

Critères QA obligatoires avant JSON final :
- Les fichiers obligatoires index.html, styles.css et script.js doivent être complets, non tronqués, directement exécutables.
- Aucun Lorem Ipsum, aucun placeholder générique, aucun lien cassé vers des assets inexistants.
- Tous les IDs de navigation correspondent à des sections existantes.
- Le rendu doit être crédible sur mobile, tablette et desktop.

Le contenu doit être en français, professionnel, persuasif, adapté au secteur du brief."""


def generate_site_single_shot(
    brief: dict[str, Any],
    on_progress: ProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    """Génère un site complet via un seul appel DeepSeek avec progression."""

    def _emit(step: str, status: str, progress: int, label: str, **extra: Any) -> None:
        if on_progress is None:
            return
        event = {
            "step": step,
            "status": status,
            "progress": progress,
            "label": label,
            "timestamp": datetime.utcnow().isoformat(),
            **extra,
        }
        try:
            on_progress(event)
        except Exception:
            pass

    started_total = time.time()
    _emit("analysis", "running", 5, "Analyse du brief")

    if not settings.deepseek_api_key:
        _emit("fallback", "running", 30, "Mode local (sans clé DeepSeek)")
        agents, output, sections, files = fallback_site_payload(brief)
        _emit("done", "ok", 100, "Site généré (fallback)", files=len(files))
        return agents, output, sections, files

    _emit("design", "running", 15, "Préparation du prompt designer")
    _emit("content", "running", 30, "Appel DeepSeek (design + contenu + code)")

    try:
        output, usage, duration_ms = _deepseek_call(
            _SINGLE_SHOT_PROMPT,
            {"brief": brief},
        )
    except Exception as exc:
        _emit("error", "failed", 100, f"Erreur DeepSeek : {exc}")
        agents, fb_output, sections, files = fallback_site_payload(brief)
        agents.insert(0, {
            "id": "agent-architect",
            "name": "architect",
            "status": "failed",
            "model": settings.deepseek_model,
            "duration_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "input": brief,
            "output": {},
            "warnings": [str(exc)],
            "error": str(exc),
            "created_at": datetime.utcnow().isoformat(),
        })
        return agents, fb_output, sections, files

    _emit("parsing", "running", 75, "Lecture de la réponse")

    design_tokens = output.get("design_tokens") or {}
    sections_raw = output.get("sections") or []
    files_raw = output.get("files") or []
    seo = output.get("seo") or {}

    sections: list[dict[str, Any]] = []
    for idx, item in enumerate(sections_raw):
        if not isinstance(item, dict):
            continue
        sections.append({
            "id": str(item.get("id") or f"section-{idx}"),
            "title": str(item.get("title") or ""),
            "content": str(item.get("content") or ""),
            "enabled": bool(item.get("enabled", True)),
        })

    files: list[dict[str, str]] = []
    for item in files_raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        content = item.get("content")
        if path and isinstance(content, str):
            files.append({"path": path, "content": content})

    _emit("assembly", "running", 90, "Assemblage des fichiers", files=len(files))

    if not files:
        _emit("repair", "running", 92, "Aucun fichier produit, fallback HTML")
        _, _, _, fb_files = fallback_site_payload(brief)
        files = fb_files

    file_paths = {f["path"] for f in files}
    missing_required = {"index.html", "styles.css", "script.js"} - file_paths
    if missing_required:
        _emit("repair", "running", 94, "Réparation des fichiers obligatoires", missing=list(missing_required))
        _, _, _, fb_files = fallback_site_payload(brief)
        fb_by_path = {f["path"]: f for f in fb_files}
        files.extend(fb_by_path[path] for path in sorted(missing_required) if path in fb_by_path)

    if not sections:
        sections = [
            {"id": "hero", "title": "Accueil", "content": brief.get("business_name", "Bienvenue"), "enabled": True},
            {"id": "contact", "title": "Contact", "content": "Contactez-nous.", "enabled": True},
        ]

    agent = {
        "id": "agent-architect",
        "name": "architect",
        "status": "ok",
        "model": settings.deepseek_model,
        "duration_ms": duration_ms,
        "tokens_in": usage["tokens_in"],
        "tokens_out": usage["tokens_out"],
        "input": brief,
        "output": {"design_tokens": design_tokens, "sections_count": len(sections), "files": [f["path"] for f in files], "seo": seo},
        "warnings": [],
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
    }

    final_output = {
        "site_schema": {"pages": 1, "sections": len(sections), "sections_data": sections},
        "design_tokens": design_tokens,
        "seo": seo,
        "generated_files": files,
    }

    total_ms = int((time.time() - started_total) * 1000)
    _emit("done", "ok", 100, f"Site généré en {total_ms / 1000:.1f}s", files=len(files), duration_ms=total_ms)

    return [agent], final_output, sections, files


def generate_project_plan(brief: dict[str, Any]) -> dict[str, Any]:
    """Génère un plan de tâches détaillé basé sur le brief d'onboarding."""
    business = brief.get("business_name") or "Mon Projet"
    sector = brief.get("sector") or "Services"
    description = brief.get("brief") or ""
    
    plan_prompt = f"""Tu es un gestionnaire de projet expert. Crée un plan de tâches détaillé pour la création d'un site web professionnel.

Contexte du projet:
- Entreprise: {business}
- Secteur: {sector}
- Description: {description}

Génère un JSON avec la structure suivante:
{{
  "title": "Plan de création du site {business}",
  "phases": [
    {{
      "phase": "Analyse & Design",
      "duration": "2-3 jours",
      "tasks": [
        {{"id": "task-1", "title": "Analyse du brief", "status": "pending", "priority": "high"}},
        {{"id": "task-2", "title": "Création de la palette de couleurs", "status": "pending", "priority": "high"}},
        {{"id": "task-3", "title": "Wireframes des pages principales", "status": "pending", "priority": "high"}}
      ]
    }},
    {{
      "phase": "Contenu & Rédaction",
      "duration": "3-4 jours",
      "tasks": [
        {{"id": "task-4", "title": "Rédaction du hero et CTA", "status": "pending", "priority": "high"}},
        {{"id": "task-5", "title": "Développement des sections", "status": "pending", "priority": "high"}},
        {{"id": "task-6", "title": "Optimisation SEO", "status": "pending", "priority": "medium"}}
      ]
    }},
    {{
      "phase": "Développement",
      "duration": "4-5 jours",
      "tasks": [
        {{"id": "task-7", "title": "Développement HTML/CSS", "status": "pending", "priority": "high"}},
        {{"id": "task-8", "title": "Intégration JavaScript", "status": "pending", "priority": "high"}},
        {{"id": "task-9", "title": "Tests responsivité", "status": "pending", "priority": "high"}}
      ]
    }},
    {{
      "phase": "Revue & Déploiement",
      "duration": "1-2 jours",
      "tasks": [
        {{"id": "task-10", "title": "Revue qualité", "status": "pending", "priority": "high"}},
        {{"id": "task-11", "title": "Optimisation performance", "status": "pending", "priority": "medium"}},
        {{"id": "task-12", "title": "Déploiement en production", "status": "pending", "priority": "high"}}
      ]
    }}
  ],
  "timeline": "10-14 jours",
  "team": ["Designer", "Copywriter", "Frontend Developer", "SEO Specialist", "QA"],
  "deliverables": [
    "Design system complet",
    "Contenu optimisé",
    "Site responsive",
    "Rapports SEO",
    "Documentation"
  ]
}}

Retourne UNIQUEMENT le JSON, sans explications."""

    if not settings.deepseek_api_key:
        return _fallback_project_plan(brief)
    
    try:
        response = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": plan_prompt}],
                "temperature": 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        try:
            plan = json.loads(content)
        except json.JSONDecodeError:
            return _fallback_project_plan(brief)
        
        return plan
    except Exception:
        return _fallback_project_plan(brief)


def _fallback_project_plan(brief: dict[str, Any]) -> dict[str, Any]:
    """Plan par défaut si DeepSeek n'est pas disponible."""
    business = brief.get("business_name") or "Mon Projet"
    return {
        "title": f"Plan de création du site {business}",
        "phases": [
            {
                "phase": "Analyse & Design",
                "duration": "2-3 jours",
                "tasks": [
                    {"id": "task-1", "title": "Analyse du brief", "status": "pending", "priority": "high"},
                    {"id": "task-2", "title": "Création de la palette de couleurs", "status": "pending", "priority": "high"},
                    {"id": "task-3", "title": "Wireframes des pages principales", "status": "pending", "priority": "high"},
                ],
            },
            {
                "phase": "Contenu & Rédaction",
                "duration": "3-4 jours",
                "tasks": [
                    {"id": "task-4", "title": "Rédaction du hero et CTA", "status": "pending", "priority": "high"},
                    {"id": "task-5", "title": "Développement des sections", "status": "pending", "priority": "high"},
                    {"id": "task-6", "title": "Optimisation SEO", "status": "pending", "priority": "medium"},
                ],
            },
            {
                "phase": "Développement",
                "duration": "4-5 jours",
                "tasks": [
                    {"id": "task-7", "title": "Développement HTML/CSS", "status": "pending", "priority": "high"},
                    {"id": "task-8", "title": "Intégration JavaScript", "status": "pending", "priority": "high"},
                    {"id": "task-9", "title": "Tests responsivité", "status": "pending", "priority": "high"},
                ],
            },
            {
                "phase": "Revue & Déploiement",
                "duration": "1-2 jours",
                "tasks": [
                    {"id": "task-10", "title": "Revue qualité", "status": "pending", "priority": "high"},
                    {"id": "task-11", "title": "Optimisation performance", "status": "pending", "priority": "medium"},
                    {"id": "task-12", "title": "Déploiement en production", "status": "pending", "priority": "high"},
                ],
            },
        ],
        "timeline": "10-14 jours",
        "team": ["Designer", "Copywriter", "Frontend Developer", "SEO Specialist", "QA"],
        "deliverables": [
            "Design system complet",
            "Contenu optimisé",
            "Site responsive",
            "Rapports SEO",
            "Documentation",
        ],
    }
