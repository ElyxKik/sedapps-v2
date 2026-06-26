"""
Site-generation workflow — DAG of agents producing static HTML.

Execution plan :
  1. designer                                    (design tokens)
     └─ [premium] strategy_director
  2. (in parallel) copywriter + seo + form_builder [+ cms_builder if has_blog]
  3. site_planner                                (multi-page architecture)
     └─ [premium] ux_architect
  4. static_page_builder × N pages               (parallel + sequential retry)
  5. animation_director                          (preset assignments)
  6. analytics_setup                             (deterministic)
  7. blog_writer × 3                             (optional, only if brief.has_blog)
  8. _assemble_static_files                      (CSS + JS + animation injection)
  9. [premium] premium_qa → [if <85] refinement → premium_qa
 10. qa (deterministic) → [if <75] refinement → qa
 11. brand_compliance + uniqueness validators
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from app.agents import (
    AGENT_REGISTRY,
    AgentInput,
    AnimationDirectorAgent,
    AnalyticsSetupAgent,
    BlogWriterAgent,
    CMSBuilderAgent,
    CopywriterAgent,
    DesignerAgent,
    FormBuilderAgent,
    QAAgent,
    SEOAgent,
    SitePlannerAgent,
    StaticPageBuilderAgent,
    StrategyDirectorAgent,
    UXArchitectAgent,
    PremiumQAAgent,
    RefinementAgent,
)
from app.celery_app import celery
from app.core_client import CoreApiClient
from app.quality.brand_compliance import validate_brand_compliance
from app.quality.uniqueness import compute_uniqueness_score
from app.workflows.generation_tiers import get_generation_rules

log = logging.getLogger(__name__)

_EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)


async def _run_agent(
    agent, ctx: dict[str, Any], inp_base: AgentInput, core: CoreApiClient, job_id: str
) -> tuple[str, dict[str, Any], dict[str, int]]:
    inp = AgentInput(
        project_id=inp_base.project_id,
        job_id=inp_base.job_id,
        tenant_id=inp_base.tenant_id,
        locale=inp_base.locale,
        context=ctx,
        params=inp_base.params,
    )
    out = await agent.run(inp)
    core.record_run(
        job_id,
        {
            "agent_name": out.agent,
            "model": out.model,
            "prompt_version": getattr(agent, "prompt_version", 1),
            "status": out.status,
            "duration_ms": out.duration_ms,
            "tokens_in": out.tokens.prompt,
            "tokens_out": out.tokens.completion,
            "input": {"context_keys": list(ctx.keys())},
            "output": out.data,
            "warnings": out.warnings,
        },
    )
    return out.agent, out.data, {"in": out.tokens.prompt, "out": out.tokens.completion}


async def _orchestrate(
    job_id: str, project_id: str, tenant_id: str, brief: dict[str, Any], locale: str
) -> dict[str, Any]:
    core = CoreApiClient()
    core.job_start(job_id)

    inp_base = AgentInput(
        project_id=project_id,
        job_id=job_id,
        tenant_id=tenant_id,
        locale=locale,
        context={"brief": brief},
        params={},
    )
    context: dict[str, Any] = {"brief": brief}
    rules = get_generation_rules(brief)
    context["generation_rules"] = rules
    total_in = total_out = 0
    core.record_event(
        job_id,
        {
            "step": "flow_select",
            "label": "Analyse de votre projet…" if brief.get("premium") else "Préparation de votre site…",
            "status": "running",
            "progress": 6,
        },
    )

    async def step(agent, current_ctx):
        progress_by_agent = {
            "designer": 8,
            "copywriter": 24,
            "seo": 38,
            "form_builder": 48,
            "cms_builder": 58,
            "site_planner": 64,
            "static_page_builder": 72,
            "animation_director": 80,
            "analytics_setup": 82,
            "strategy_director": 14,
            "ux_architect": 67,
            "premium_qa": 94,
            "refinement_agent": 96,
            "qa": 92,
        }
        label_by_agent = {
            "designer": "Création de votre identité visuelle…",
            "copywriter": "Rédaction des textes de votre site…",
            "seo": "Optimisation pour les moteurs de recherche…",
            "form_builder": "Mise en place des formulaires de contact…",
            "cms_builder": "Organisation de la structure du contenu…",
            "site_planner": "Planification de l'architecture du site…",
            "static_page_builder": "Construction des pages…",
            "animation_director": "Ajout des animations et effets visuels…",
            "analytics_setup": "Configuration du suivi de performance…",
            "strategy_director": "Définition de la stratégie de votre marque…",
            "ux_architect": "Optimisation de l'expérience utilisateur…",
            "premium_qa": "Contrôle qualité avancé…",
            "refinement_agent": "Finalisation et polish de votre site…",
            "qa": "Vérification qualité finale…",
        }
        core.record_event(
            job_id,
            {
                "step": getattr(agent, "name", "agent"),
                "label": label_by_agent.get(
                    getattr(agent, "name", ""), f"Agent {getattr(agent, 'name', 'IA')} en cours…"
                ),
                "status": "running",
                "progress": progress_by_agent.get(getattr(agent, "name", ""), 50),
            },
        )
        name, data, toks = await _run_agent(agent, current_ctx, inp_base, core, job_id)
        return name, data, toks

    # 1. Designer
    name, data, t = await step(DesignerAgent(), context)
    total_in += t["in"]
    total_out += t["out"]
    context[name] = data

    if brief.get("premium"):
        name, data, t = await step(StrategyDirectorAgent(), context)
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]

    # 2. Parallel : copywriter, seo, form_builder, cms_builder (last optional)
    parallel_agents = [CopywriterAgent(), SEOAgent(), FormBuilderAgent()]
    if brief.get("has_blog"):
        parallel_agents.append(CMSBuilderAgent())

    results = await asyncio.gather(
        *[step(a, context) for a in parallel_agents], return_exceptions=False
    )
    for name, data, t in results:
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]

    # 3. Site planner (decides multi-page architecture before HTML generation)
    name, data, t = await step(SitePlannerAgent(), context)
    context[name] = data
    site_plan = data
    total_in += t["in"]
    total_out += t["out"]

    if brief.get("premium"):
        name, data, t = await step(UXArchitectAgent(), context)
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]

    # 4. Page-by-page generation (in parallel)
    page_outputs: list[dict[str, Any]] = []
    pages = site_plan.get("pages", [])
    if pages:
        core.record_event(
            job_id,
            {
                "step": "static_page_builder",
                "label": f"Génération en parallèle de {len(pages)} pages...",
                "status": "running",
                "progress": 66,
            },
        )
        
        async def build_page(index: int, p: dict[str, Any]):
            inp = AgentInput(
                project_id=project_id,
                job_id=job_id,
                tenant_id=tenant_id,
                locale=locale,
                context=context,
                params={"page": p},
            )
            out = await StaticPageBuilderAgent().run(inp)
            core.record_run(
                job_id,
                {
                    "agent_name": out.agent,
                    "model": out.model,
                    "status": out.status,
                    "duration_ms": out.duration_ms,
                    "tokens_in": out.tokens.prompt,
                    "tokens_out": out.tokens.completion,
                    "input": {"page": p},
                    "output": out.data,
                    "warnings": out.warnings,
                },
            )
            return out

        page_results = await asyncio.gather(*[build_page(i, p) for i, p in enumerate(pages)], return_exceptions=True)
        for out in page_results:
            if isinstance(out, BaseException):
                log.error("page build crashed: %s", out)
                continue
            total_in += out.tokens.prompt
            total_out += out.tokens.completion
            if out.status != "failed":
                page_outputs.append(out.data)

        # Retry séquentiel des pages manquantes (une seule fois)
        built_paths = {p.get("path") for p in page_outputs}
        missing = [p for p in pages if (p.get("path") or "index.html") not in built_paths]
        for p in missing:
            try:
                out = await build_page(0, p)
                total_in += out.tokens.prompt
                total_out += out.tokens.completion
                if out.status != "failed":
                    page_outputs.append(out.data)
            except Exception as e:  # noqa: BLE001
                log.error("page retry failed for %s: %s", p.get("path"), e)

    if not page_outputs:
        raise RuntimeError("site_generation: aucune page HTML n'a pu être générée")
    context["static_pages"] = {"pages": page_outputs}

    # 5. Animation director (chooses controlled presets, not random effects)
    name, data, t = await step(AnimationDirectorAgent(), context)
    context[name] = data
    total_in += t["in"]
    total_out += t["out"]

    # 6. Analytics setup (deterministic)
    name, data, t = await step(AnalyticsSetupAgent(), context)
    context[name] = data
    total_in += t["in"]
    total_out += t["out"]

    # 7. Blog writer (3 seed articles in parallel, optional)
    if brief.get("has_blog"):
        cms = context.get("cms_builder", {})
        cats = cms.get("categories") or [{"slug": "general", "name": "Général"}]
        topics = [
            {
                "topic": f"Guide complet : tout savoir sur le secteur {brief.get('sector', '')}",
                "target_keyword": brief.get("sector", ""),
                "category": cats[0]["slug"],
                "length": 1500,
            },
            {
                "topic": f"5 conseils essentiels pour {brief.get('target_audience', 'nos clients')}",
                "target_keyword": "conseils",
                "category": cats[0]["slug"],
                "length": 1200,
            },
            {
                "topic": f"Pourquoi choisir {brief.get('business_name', 'notre marque')} : notre approche unique",
                "target_keyword": brief.get("business_name", ""),
                "category": cats[0]["slug"],
                "length": 1800,
            },
        ]
        
        async def build_article(t_):
            inp = AgentInput(
                project_id=project_id,
                job_id=job_id,
                tenant_id=tenant_id,
                locale=locale,
                context={"brief": brief},
                params=t_,
            )
            out = await BlogWriterAgent().run(inp)
            core.record_run(
                job_id,
                {
                    "agent_name": out.agent,
                    "model": out.model,
                    "status": out.status,
                    "duration_ms": out.duration_ms,
                    "tokens_in": out.tokens.prompt,
                    "tokens_out": out.tokens.completion,
                    "input": t_,
                    "output": out.data,
                    "warnings": out.warnings,
                },
            )
            return out

        seed_articles = []
        article_results = await asyncio.gather(*[build_article(t_) for t_ in topics], return_exceptions=False)
        for out in article_results:
            total_in += out.tokens.prompt
            total_out += out.tokens.completion
            if out.status != "failed":
                seed_articles.append(out.data)
        context["blog_writer"] = {"articles": seed_articles}

    static_files = _assemble_static_files(context)
    context["static_site"] = {
        "generated_files": static_files,
        "files": static_files,
        "sections": _collect_sections(page_outputs),
        "pages": site_plan.get("pages", []),
    }

    refinements: list[str] = []

    async def apply_refinement() -> None:
        nonlocal total_in, total_out, refinements
        name, data, t = await step(RefinementAgent(), context)
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]
        refined_files = data.get("files") if isinstance(data, dict) else None
        if isinstance(refined_files, list) and refined_files:
            context["static_site"]["generated_files"] = refined_files
            context["static_site"]["files"] = refined_files
            refinements = data.get("changes") if isinstance(data.get("changes"), list) else []

    if brief.get("premium"):
        name, data, t = await step(PremiumQAAgent(), context)
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]

        premium_score = int((context.get("premium_qa") or {}).get("score", 0) or 0)
        if premium_score < rules["qa_min_score"]:
            await apply_refinement()

            name, data, t = await step(PremiumQAAgent(), context)
            context[name] = data
            total_in += t["in"]
            total_out += t["out"]

    # 8. QA
    name, data, t = await step(QAAgent(), context)
    context[name] = data
    total_in += t["in"]
    total_out += t["out"]

    # 8b. Boucle de correction standard : si le QA déterministe est sous le seuil,
    # une passe de raffinement est tentée puis le QA est rejoué.
    qa_score_first = int((context.get("qa") or {}).get("score", 0) or 0)
    if not brief.get("premium") and qa_score_first < rules["qa_min_score"]:
        await apply_refinement()
        name, data, t = await step(QAAgent(), context)
        context[name] = data
        total_in += t["in"]
        total_out += t["out"]

    # 8c. Brand compliance & uniqueness validators
    static_site_for_check = context.get("static_site", {})
    generated_files_for_check = static_site_for_check.get("generated_files") or static_site_for_check.get("files") or []
    design_tokens_for_check = static_site_for_check.get("design_tokens") or context.get("designer", {})
    brand_result = validate_brand_compliance(brief, design_tokens_for_check, generated_files_for_check)
    uniqueness_result = compute_uniqueness_score(generated_files_for_check, brief)
    context["brand_compliance"] = brand_result
    context["uniqueness_score"] = uniqueness_result
    core.record_event(
        job_id,
        {
            "step": "quality_validators",
            "label": "Validation marque et unicité…",
            "status": "running",
            "progress": 90,
        },
    )
    if brand_result["issues"]:
        log.warning("job=%s brand_compliance issues: %s", job_id, brand_result["issues"])
    if uniqueness_result["issues"]:
        log.warning("job=%s uniqueness issues: %s", job_id, uniqueness_result["issues"])

    # Final job output
    static_site = context.get("static_site", {})
    final = {
        "render_mode": "static_classic",
        "quality_tier": rules["quality_tier"],
        "premium": bool(brief.get("premium")),
        "stack": brief.get("stack") or "onepage",
        "generated_files": static_site.get("generated_files", []),
        "files": static_site.get("files", []),
        "sections": static_site.get("sections", []),
        "pages": static_site.get("pages", []),
        "design_tokens": static_site.get("design_tokens", {}) or context.get("designer", {}),
        "strategy": context.get("strategy_director", {}),
        "ux_architecture": context.get("ux_architect", {}),
        "animation": context.get("animation_director", {}),
        "seo": context.get("seo", {}),
        "form": context.get("form_builder", {}),
        "analytics": context.get("analytics_setup", {}),
        "cms": context.get("cms_builder", {}),
        "articles": context.get("blog_writer", {}).get("articles", []),
        "premium_qa": context.get("premium_qa", {}),
        "refinements": refinements,
        "qa": context.get("qa", {}),
        "brand_compliance": context.get("brand_compliance", {}),
        "uniqueness_score": context.get("uniqueness_score", {}),
    }

    qa_score = int((context.get("qa") or {}).get("score", 0) or 0)
    min_score = rules["qa_min_score"]
    if brief.get("premium"):
        premium_score = int((context.get("premium_qa") or {}).get("score", 0) or 0)
        effective_score = min(qa_score, premium_score)
    else:
        effective_score = qa_score
    status = "success" if effective_score >= min_score else "degraded"

    core.job_complete(
        job_id,
        {
            "status": status,
            "error": None,
            "output": final,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "cost_cents": 0,
        },
    )
    return final


def _collect_sections(page_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for page in page_outputs:
        path = page.get("path")
        for section in page.get("sections") or []:
            if isinstance(section, dict):
                item = dict(section)
                item["page_path"] = path
                sections.append(item)
    return sections


def _assemble_static_files(context: dict[str, Any]) -> list[dict[str, str]]:
    pages = context.get("static_pages", {}).get("pages", [])
    allow_emoji = _brief_allows_emoji(context.get("brief", {}))
    files: list[dict[str, str]] = []
    seen: set[str] = set()
    for page in pages:
        path = str(page.get("path") or "").strip().lstrip("/")
        html = page.get("html")
        if not path or not isinstance(html, str) or path in seen:
            continue
        seen.add(path)
        html = _apply_animation_assignments(html, path, context.get("animation_director", {}))
        if not allow_emoji:
            html = _strip_emojis(html)
        files.append({"path": path, "content": html})
    files.append({"path": "styles.css", "content": _shared_css(context)})
    files.append({"path": "script.js", "content": _shared_js()})
    return files



_VIBE_CSS: dict[str, str] = {
    "premium": """
.hero{background:radial-gradient(ellipse at top,rgba(0,0,0,.4),transparent 60%),linear-gradient(180deg,#0f0f0f,#1a1a2e)!important}
.card{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);backdrop-filter:blur(12px)}
.card:hover{box-shadow:0 24px 80px rgba(0,0,0,.4);border-color:rgba(255,255,255,.14)}
.eyebrow{letter-spacing:.2em;font-size:.8rem}
h1{letter-spacing:-.08em}
.button,.btn{border-radius:8px;font-weight:700;letter-spacing:.02em;padding:16px 32px}
.section{padding:100px 7vw}
.grid{gap:32px}
.card{padding:36px}
""",
    "minimal": """
.hero{background:linear-gradient(180deg,#fff,#fafafa)!important;padding:80px 7vw 60px}
.card{border:1px solid #eee;box-shadow:none}
.card:hover{box-shadow:0 2px 12px rgba(0,0,0,.06)}
.eyebrow{letter-spacing:.1em;font-size:.75rem;color:#999}
h1{letter-spacing:-.05em;font-weight:600}
h2{font-weight:600}
.button,.btn{border-radius:6px;font-weight:600;padding:12px 28px}
.section{padding:80px 7vw}
p{color:#666}
""",
    "fun": """
.hero{background:radial-gradient(circle at 20% 80%,rgba(245,158,11,.15),transparent 40%),radial-gradient(circle at 80% 20%,rgba(34,211,238,.12),transparent 40%),linear-gradient(135deg,#fff,#fef3c7)!important}
.card{border:2px solid #fde68a;border-radius:20px}
.card:hover{transform:translateY(-8px) rotate(-1deg);box-shadow:0 16px 40px rgba(245,158,11,.2)}
.eyebrow{color:var(--accent);font-size:.85rem;letter-spacing:.08em}
h1{letter-spacing:-.04em}
.button,.btn{border-radius:999px;font-weight:800;padding:16px 28px}
.section{padding:72px 7vw}
.grid{gap:20px}
""",
    "corporate": """
.hero{background:linear-gradient(135deg,#f8fafc,#e2e8f0)!important;padding:90px 7vw 70px}
.card{border:1px solid #cbd5e1;border-radius:8px}
.card:hover{box-shadow:0 8px 24px rgba(0,0,0,.08);transform:translateY(-2px)}
.eyebrow{letter-spacing:.16em;font-size:.78rem;color:var(--primary)}
h1{letter-spacing:-.06em;font-weight:800}
h2{font-weight:700}
.button,.btn{border-radius:6px;font-weight:700;padding:14px 28px}
.section{padding:88px 7vw}
p{color:#475569}
.grid{gap:24px}
""",
    "moderne": """
.hero{background:radial-gradient(circle at top right,rgba(37,99,235,.18),transparent 34%),linear-gradient(135deg,#fff,#eff6ff)}
.card{border:1px solid var(--line);border-radius:var(--radius)}
.card:hover{transform:translateY(-4px);box-shadow:0 16px 48px rgba(0,0,0,.12)}
""",
}


def _shared_css(context: dict[str, Any]) -> str:
    designer = context.get("designer", {}) if isinstance(context.get("designer"), dict) else {}
    # La structure du designer est : {"palette": {...}, "typography": {...}, "spacing": {...}, "radius": {...}}
    palette = designer.get("palette") if isinstance(designer.get("palette"), dict) else {}
    typography = designer.get("typography") if isinstance(designer.get("typography"), dict) else {}
    spacing = designer.get("spacing") if isinstance(designer.get("spacing"), dict) else {}
    radius_tokens = designer.get("radius") if isinstance(designer.get("radius"), dict) else {}

    primary = palette.get("primary") or "#2563eb"
    secondary = palette.get("secondary") or "#0f172a"
    accent = palette.get("accent") or "#f59e0b"
    bg = palette.get("bg") or "#f8fafc"
    surface = palette.get("surface") or "#ffffff"
    text_color = palette.get("text") or "#0f172a"
    muted = palette.get("muted") or "#64748b"

    font_heading = typography.get("heading") or "Inter"
    font_body = typography.get("body") or "Inter"
    scale = typography.get("scale") if isinstance(typography.get("scale"), dict) else {}
    h1_size = scale.get("h1") or "2.5rem"
    h2_size = scale.get("h2") or "2rem"
    h3_size = scale.get("h3") or "1.5rem"

    radius_lg = radius_tokens.get("lg") or "16px"
    radius_md = radius_tokens.get("md") or "10px"
    radius_full = radius_tokens.get("full") or "9999px"

    # Espacements
    sp_xl = spacing.get("xl") or "32px"
    sp_2xl = spacing.get("2xl") or "48px"

    # Google Fonts — charger heading et body (dédupliqué si identiques)
    fonts_to_load = list(dict.fromkeys([font_heading, font_body]))  # préserve l'ordre, retire les doublons
    google_fonts_url = "https://fonts.googleapis.com/css2?" + "&".join(
        f"family={f.replace(' ', '+')}:wght@400;500;600;700;800;900"
        for f in fonts_to_load
        if f and f.lower() not in ("system-ui", "sans-serif", "serif", "monospace")
    ) + "&display=swap"
    font_import = f"@import url('{google_fonts_url}');\n" if fonts_to_load else ""
    vibe = str(designer.get("vibe") or "moderne").lower()


    return font_import + f""":root{{--primary:{primary};--secondary:{secondary};--accent:{accent};--bg:{bg};--surface:{surface};--text:{text_color};--muted:{muted};--line:#e2e8f0;--radius:{radius_lg};--radius-md:{radius_md};--radius-full:{radius_full};--sp-xl:{sp_xl};--sp-2xl:{sp_2xl};--font-heading:'{font_heading}',system-ui,sans-serif;--font-body:'{font_body}',system-ui,sans-serif}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text)}}a{{color:inherit}}.site-header{{position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;align-items:center;gap:24px;padding:18px 7vw;background:rgba(255,255,255,.84);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}}.brand{{font-weight:900;text-decoration:none;letter-spacing:-.03em}}.navbar{{display:flex;gap:22px;align-items:center}}.nav-link{{text-decoration:none;color:var(--muted);font-weight:700}}.nav-link:hover{{color:var(--primary)}}.hero,.component-hero-split,.component-hero-centered{{padding:110px 7vw 90px;background:radial-gradient(circle at top right,rgba(37,99,235,.18),transparent 34%),linear-gradient(135deg,#fff,#eff6ff)}}.eyebrow{{color:var(--primary);font-weight:900;letter-spacing:.14em;text-transform:uppercase}}h1{{max-width:980px;font-size:clamp(42px,7vw,84px);line-height:.94;letter-spacing:-.07em;margin:16px 0}}h2{{font-size:clamp(28px,4vw,52px);letter-spacing:-.04em;margin:0 0 18px}}p{{font-size:18px;line-height:1.75;color:#475569}}.button,.btn,button{{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:999px;background:var(--secondary);color:#fff;padding:15px 24px;text-decoration:none;font-weight:900;cursor:pointer;transition:transform .25s ease,box-shadow .25s ease,background .25s ease}}.section,.component-section{{padding:82px 7vw}}.grid,.component-features-grid,.component-gallery-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;padding:82px 7vw}}.card,.grid article,.component-card,.component-service-card,.component-review-card{{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:32px;box-shadow:0 24px 70px rgba(15,23,42,.08)}}.component-cta-section,.cta{{margin:40px 7vw;padding:54px;border-radius:34px;background:var(--secondary);color:#fff}}.component-cta-section p,.cta p{{color:#cbd5e1}}.component-contact-form,.contact{{margin:50px 7vw;padding:40px;border:1px solid var(--line);border-radius:var(--radius);background:#fff}}form{{display:grid;gap:14px;max-width:680px}}input,textarea,select{{width:100%;border:1px solid #cbd5e1;border-radius:16px;padding:14px 16px;font:inherit}}textarea{{min-height:140px}}.footer,.component-footer{{padding:48px 7vw;text-align:center;color:var(--muted);border-top:1px solid var(--line)}}[data-animate]{{opacity:0;transition-property:opacity,transform;transition-timing-function:cubic-bezier(.22,1,.36,1);transition-duration:var(--motion-duration,.65s);transition-delay:var(--motion-delay,0s);will-change:opacity,transform}}[data-animate].is-visible{{opacity:1;transform:none}}[data-animate='fade-up']{{transform:translate3d(0,28px,0)}}[data-animate='fade-down']{{transform:translate3d(0,-28px,0)}}[data-animate='fade-left']{{transform:translate3d(28px,0,0)}}[data-animate='fade-right']{{transform:translate3d(-28px,0,0)}}[data-animate='zoom-in']{{transform:scale(.96)}}[data-animate='scale-in']{{transform:scale(.92)}}[data-animate='fade-in']{{transform:none}}.motion-lift-hover{{transition:transform .25s ease,box-shadow .25s ease}}.motion-lift-hover:hover{{transform:translate3d(0,-6px,0);box-shadow:0 30px 80px rgba(15,23,42,.14)}}.motion-glow-hover:hover{{box-shadow:0 0 0 1px rgba(37,99,235,.18),0 24px 80px rgba(37,99,235,.22)}}.motion-button-expand:hover{{transform:scale(1.035)}}.motion-underline-slide{{background-image:linear-gradient(currentColor,currentColor);background-size:0 2px;background-position:0 100%;background-repeat:no-repeat;transition:background-size .25s ease}}.motion-underline-slide:hover{{background-size:100% 2px}}.motion-stagger-children>*{{transition-delay:calc(var(--motion-delay,0s) + var(--stagger-index,0)*var(--motion-stagger,.06s))}}.motion-gradient-shift{{background-size:200% 200%;animation:gradientShift 12s ease infinite}}@keyframes gradientShift{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}@media(max-width:820px){{.navbar{{display:none}}.grid,.component-features-grid,.component-gallery-grid{{grid-template-columns:1fr;padding:54px 6vw}}.hero,.component-hero-split,.component-hero-centered{{padding:78px 6vw 62px}}.site-header{{padding:16px 6vw}}[data-animate]{{transition-duration:.45s;transform:translate3d(0,14px,0)}}}}@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important;scroll-behavior:auto!important}}[data-animate]{{opacity:1!important;transform:none!important}}}}""" + _VIBE_CSS.get(vibe, _VIBE_CSS["moderne"])


def _shared_js() -> str:
    return """document.querySelectorAll('a[href^="#"]').forEach(anchor=>anchor.addEventListener('click',event=>{const target=document.querySelector(anchor.getAttribute('href'));if(target){event.preventDefault();target.scrollIntoView({behavior:'smooth',block:'start'});}}));document.querySelectorAll('[data-animate]').forEach((el)=>{if(el.dataset.stagger){Array.from(el.children).forEach((child,index)=>child.style.setProperty('--stagger-index',index));}});const motionObserver=new IntersectionObserver((entries)=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');motionObserver.unobserve(entry.target);}})},{threshold:.16,rootMargin:'0px 0px -8% 0px'});document.querySelectorAll('[data-animate]').forEach(el=>motionObserver.observe(el));document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',event=>{event.preventDefault();const status=form.querySelector('[data-form-status]');if(status){status.textContent='Merci, votre message a été préparé.';}else{alert('Merci, votre message a été préparé.');}}));"""


def _apply_animation_assignments(html: str, path: str, animation_director: dict[str, Any]) -> str:
    assignments = animation_director.get("assignments") if isinstance(animation_director, dict) else []
    if not isinstance(assignments, list):
        return html
    updated = html
    for item in assignments:
        if not isinstance(item, dict) or item.get("page_path") != path:
            continue
        section_id = str(item.get("section_id") or "").strip()
        if not section_id:
            continue
        animation = item.get("animation") if isinstance(item.get("animation"), dict) else {}
        enter = animation.get("enter")
        hover = animation.get("hover")
        duration = animation.get("duration", 0.65)
        delay = animation.get("delay", 0)
        stagger = animation.get("stagger", 0)
        attrs = []
        style_parts = []
        if enter:
            attrs.append(f'data-animate="{enter}"')
            style_parts.append(f"--motion-duration:{duration}s")
            style_parts.append(f"--motion-delay:{delay}s")
        if stagger:
            attrs.append(f'data-stagger="true"')
            style_parts.append(f"--motion-stagger:{stagger}s")
        if style_parts:
            attrs.append(f'style="{";".join(style_parts)}"')
        class_suffix = _hover_class(str(hover or ""))
        pattern = re.compile(rf'(<[a-zA-Z][^>]*\sid=["\']{re.escape(section_id)}["\'][^>]*)(>)')

        def repl(match: re.Match[str]) -> str:
            opening = match.group(1)
            closing = match.group(2)
            if enter and "data-animate=" not in opening:
                opening = f"{opening} {' '.join(attrs)}"
            if class_suffix:
                opening = _append_class(opening, class_suffix)
            return opening + closing

        updated = pattern.sub(repl, updated, count=1)
    return updated


def _hover_class(preset: str) -> str:
    return {
        "lift-hover": "motion-lift-hover",
        "glow-hover": "motion-glow-hover",
        "underline-slide": "motion-underline-slide",
        "button-expand": "motion-button-expand",
    }.get(preset, "")


def _append_class(opening_tag: str, class_name: str) -> str:
    class_match = re.search(r'class=["\']([^"\']*)["\']', opening_tag)
    if class_match:
        classes = class_match.group(1)
        if class_name in classes.split():
            return opening_tag
        replacement = f'class="{classes} {class_name}"'
        return opening_tag[: class_match.start()] + replacement + opening_tag[class_match.end() :]
    return f'{opening_tag} class="{class_name}"'


def _brief_allows_emoji(brief: dict[str, Any]) -> bool:
    text = " ".join(str(value).lower() for value in brief.values() if isinstance(value, str))
    return "emoji" in text or "emojis" in text


def _strip_emojis(value: str) -> str:
    return _EMOJI_RE.sub("", value)


@celery.task(name="workflows.site_generation", bind=True, max_retries=1)
def run_site_generation(
    self, job_id: str, project_id: str, tenant_id: str, brief: dict[str, Any], locale: str = "fr"
) -> dict[str, Any]:
    log.info("site_generation start job=%s project=%s", job_id, project_id)
    try:
        return asyncio.run(_orchestrate(job_id, project_id, tenant_id, brief, locale))
    except Exception as e:  # noqa: BLE001
        log.exception("site_generation failed")
        try:
            CoreApiClient().job_complete(
                job_id,
                {
                    "status": "failed",
                    "error": str(e)[:1900],
                    "output": {},
                },
            )
        except Exception:
            log.exception("could not notify core-api of failure")
        raise


# Ensure registry is populated
_ = AGENT_REGISTRY
