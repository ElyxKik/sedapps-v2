"""Astro mode generator: produces a SitePayload JSON consumable by apps/astro-renderer.

The output is a single virtual file `content/site.json` containing a payload
that conforms to `@sedapps/page-schema` SitePayloadSchema.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable

from app.config import settings
from app.llm_site_generator import _agent_call  # reuse LLM client + JSON extraction

ProgressCallback = Callable[[dict[str, Any]], None]


_ASTRO_PROMPT = """You are the Site Payload Architect for SedApps Astro renderer.

Goal: from the user brief, produce a SINGLE strict JSON document conforming to the
SitePayload schema below. The Astro renderer at apps/astro-renderer will consume it
to build a static site (HTML/CSS) — there is NO HTML/CSS/JS in your output, only data.

# Allowed section types (use 4–8 per page, mix sensibly)
- "hero.split"          props: title, subtitle, cta_primary{label,href}, cta_secondary{label,href}
- "hero.center"         props: title, subtitle, cta_primary{...}, cta_secondary{...}
- "features.grid"       props: title, subtitle, columns(2|3|4), items[{title,desc,icon}]
- "about.split"         props: title, body (markdown allowed)
- "testimonials.carousel" props: title, items[{author, role, quote}]
- "pricing.table"       props: title, plans[{name,price,period,features[],cta,highlighted}]
- "faq.accordion"       props: title, items[{q,a}]
- "cta.banner"          props: title, subtitle, cta{label,href}
- "form.contact"        props: title, subtitle, form_id, layout("split"|"single")
- "blog.index"          props: title, style("grid"|"list"|"magazine"), per_page
- "richtext"            props: markdown
- "gallery.grid"        props: title, items[{url,alt}]

# Required JSON shape
{
  "page_schema": {
    "pages": [
      {
        "meta": {
          "slug": "home",
          "title": "...",
          "description": "...",
          "og": {"title":"...","description":"..."},
          "schema_org": {"@context":"https://schema.org","@type":"<LocalBusiness|Organization|Bakery|...>", "name":"..."}
        },
        "layout": {"header_id":"default","footer_id":"default"},
        "sections": [
          {"id":"hero-1","type":"hero.split","props":{...}},
          ...
        ]
      },
      {
        "meta":{"slug":"about", ...},
        "layout":{"header_id":"default","footer_id":"default"},
        "sections":[ ... ]
      }
    ]
  },
  "design_tokens": {
    "palette":{"primary":"#...","secondary":"#...","accent":"#...","bg":"#...","surface":"#...","text":"#...","muted":"#...","success":"#10B981","warning":"#F59E0B","danger":"#EF4444"},
    "typography":{"heading":"<Google Font>","body":"<Google Font>","scale":{"h1":"3rem","h2":"2rem","h3":"1.5rem","body":"1rem","small":"0.875rem"}},
    "spacing":{"xs":"4px","sm":"8px","md":"16px","lg":"24px","xl":"32px","2xl":"48px","3xl":"64px"},
    "radius":{"sm":"6px","md":"12px","lg":"20px","full":"9999px"},
    "shadow":{"sm":"0 1px 2px rgba(0,0,0,.08)","md":"0 6px 24px rgba(0,0,0,.1)","lg":"0 20px 60px rgba(0,0,0,.15)"},
    "vibe":"premium|playful|minimal|bold"
  },
  "seo":{"sitemap":{"include":["home","about"]},"robots":"User-agent: *\\nAllow: /"},
  "form":{
    "id":"contact-form","name":"Contact",
    "fields":[
      {"key":"name","label":"Nom","type":"text","required":true,"max":120},
      {"key":"email","label":"Email","type":"email","required":true},
      {"key":"message","label":"Message","type":"textarea","required":true,"max":2000}
    ],
    "submit_label":"Envoyer","success_message":"Merci !"
  },
  "analytics":{"tracker_id":"sed-demo"},
  "articles":[
    {"slug":"...","title":"...","excerpt":"...","cover_url":"","content_md":"## ...","published_at":"2026-01-01T00:00:00Z","reading_time_min":3,"seo":{}}
  ]
}

# Hard rules
- Output VALID JSON only (no markdown, no comments, no trailing text).
- Every section MUST have a unique "id" (slug-like).
- Use realistic, on-brand copy in the brief language (default: French if brief is French).
- Choose a coherent palette matching the sector (e.g., bakery=warm, fintech=cool blue, eco=green).
- Pick Google Fonts only.
- Include at least 1 page (home). Include "about" if it adds value.
- Include 2–4 articles with rich content_md (~200+ words each) when the project benefits from a blog.
- Always include `form.contact` once and matching form fields.
- Stay realistic: no lorem ipsum, no placeholders.
"""


def _astro_fallback(brief: dict[str, Any]) -> dict[str, Any]:
    business = brief.get("business_name") or brief.get("name") or "Mon Site"
    sector = brief.get("sector") or "Services"
    desc = brief.get("brief") or brief.get("description") or f"Site moderne pour {business}"
    return {
        "page_schema": {
            "pages": [
                {
                    "meta": {
                        "slug": "home",
                        "title": f"{business} — {sector}",
                        "description": desc,
                        "og": {"title": business, "description": desc},
                        "schema_org": {"@context": "https://schema.org", "@type": "Organization", "name": business},
                    },
                    "layout": {"header_id": "default", "footer_id": "default"},
                    "sections": [
                        {"id": "hero-1", "type": "hero.center", "props": {
                            "title": f"Bienvenue chez {business}",
                            "subtitle": desc,
                            "cta_primary": {"label": "Nous contacter", "href": "#contact"},
                        }},
                        {"id": "feat-1", "type": "features.grid", "props": {
                            "title": "Nos atouts", "columns": 3,
                            "items": [
                                {"title": "Qualité", "desc": "Un travail soigné et professionnel.", "icon": "✨"},
                                {"title": "Réactivité", "desc": "Une équipe disponible et à l'écoute.", "icon": "⚡"},
                                {"title": "Expertise", "desc": "Un savoir-faire reconnu dans le secteur.", "icon": "🎯"},
                            ],
                        }},
                        {"id": "cta-1", "type": "cta.banner", "props": {
                            "title": "Parlons de votre projet",
                            "subtitle": "Réponse sous 24h",
                            "cta": {"label": "Nous écrire", "href": "#contact"},
                        }},
                        {"id": "form-1", "type": "form.contact", "props": {
                            "title": "Contact", "form_id": "contact-form", "layout": "split",
                        }},
                    ],
                }
            ]
        },
        "design_tokens": {
            "palette": {
                "primary": "#6366F1", "secondary": "#EC4899", "accent": "#F59E0B",
                "bg": "#FFFFFF", "surface": "#F8FAFC", "text": "#0F172A", "muted": "#64748B",
                "success": "#10B981", "warning": "#F59E0B", "danger": "#EF4444",
            },
            "typography": {
                "heading": "Inter", "body": "Inter",
                "scale": {"h1": "3rem", "h2": "2rem", "h3": "1.5rem", "body": "1rem", "small": "0.875rem"},
            },
            "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px", "2xl": "48px", "3xl": "64px"},
            "radius": {"sm": "6px", "md": "12px", "lg": "20px", "full": "9999px"},
            "shadow": {"sm": "0 1px 2px rgba(0,0,0,.08)", "md": "0 6px 24px rgba(0,0,0,.1)", "lg": "0 20px 60px rgba(0,0,0,.15)"},
            "vibe": "premium",
        },
        "seo": {"sitemap": {"include": ["home"]}, "robots": "User-agent: *\nAllow: /"},
        "form": {
            "id": "contact-form", "name": "Contact",
            "fields": [
                {"key": "name", "label": "Nom", "type": "text", "required": True, "max": 120},
                {"key": "email", "label": "Email", "type": "email", "required": True},
                {"key": "message", "label": "Message", "type": "textarea", "required": True, "max": 2000},
            ],
            "submit_label": "Envoyer",
            "success_message": "Merci ! Nous vous répondons sous 24h.",
        },
        "analytics": {"tracker_id": ""},
        "articles": [],
    }


# ----- Lightweight validators / normalizers -----

_ALLOWED_TYPES = {
    "hero.split", "hero.center", "features.grid", "about.split",
    "testimonials.carousel", "pricing.table", "faq.accordion", "cta.banner",
    "form.contact", "blog.index", "richtext", "gallery.grid",
}

# Required props per section type (kept lightweight; renderer is forgiving)
_REQUIRED_PROPS: dict[str, list[str]] = {
    "hero.split": ["title"],
    "hero.center": ["title"],
    "features.grid": ["items"],
    "about.split": ["title", "body"],
    "testimonials.carousel": ["items"],
    "pricing.table": ["plans"],
    "faq.accordion": ["items"],
    "cta.banner": ["title"],
    "form.contact": ["form_id"],
    "blog.index": [],
    "richtext": ["markdown"],
    "gallery.grid": ["items"],
}

_HEX_RE = __import__("re").compile(r"^#[0-9A-Fa-f]{6}$")
_PLACEHOLDER_RE = __import__("re").compile(r"lorem ipsum|placeholder|votre[\s_-]+texte|à\s*compléter|tbd", __import__("re").I)


def _validate_payload(payload: dict[str, Any]) -> tuple[list[str], list[str], int]:
    """Strict-ish validation. Returns (critical_issues, warnings, score 0..100)."""
    critical: list[str] = []
    warns: list[str] = []

    if not isinstance(payload, dict):
        return ["payload is not an object"], [], 0

    pages = (payload.get("page_schema") or {}).get("pages") or []
    if not pages:
        critical.append("no pages in page_schema")

    has_form_section = False
    has_form_id = (payload.get("form") or {}).get("id")

    seen_ids: set[str] = set()
    for p in pages:
        meta = p.get("meta") or {}
        slug = meta.get("slug") or "?"
        title = meta.get("title") or ""
        desc = meta.get("description") or ""
        if not title:
            critical.append(f"page {slug}: missing title")
        elif not (10 <= len(title) <= 80):
            warns.append(f"page {slug}: title length should be 10–80 chars (got {len(title)})")
        if not (50 <= len(desc) <= 180):
            warns.append(f"page {slug}: description length should be 50–180 chars (got {len(desc)})")
        if _PLACEHOLDER_RE.search(title) or _PLACEHOLDER_RE.search(desc):
            warns.append(f"page {slug}: placeholder text detected in meta")

        sections = p.get("sections") or []
        if not sections:
            critical.append(f"page {slug}: no sections")
        for s in sections:
            sid = s.get("id")
            stype = s.get("type")
            if sid in seen_ids:
                warns.append(f"duplicate section id '{sid}'")
            else:
                seen_ids.add(sid)
            if stype not in _ALLOWED_TYPES:
                critical.append(f"page {slug}: unknown section type '{stype}'")
                continue
            props = s.get("props") or {}
            for req in _REQUIRED_PROPS.get(stype, []):
                if req not in props or props.get(req) in (None, "", [], {}):
                    critical.append(f"page {slug}: section {sid} ({stype}) missing required prop '{req}'")
            for k, v in props.items():
                if isinstance(v, str) and _PLACEHOLDER_RE.search(v):
                    warns.append(f"page {slug}: section {sid} prop '{k}' contains placeholder text")
            if stype == "form.contact":
                has_form_section = True

    # Design tokens
    palette = (payload.get("design_tokens") or {}).get("palette") or {}
    for key in ("primary", "bg", "text"):
        if not _HEX_RE.match(str(palette.get(key, ""))):
            warns.append(f"palette.{key} must be a #RRGGBB hex")

    # Form coherence
    if has_form_section and not has_form_id:
        critical.append("form.contact section present but global form has no id")

    # Articles
    for a in (payload.get("articles") or []):
        if not a.get("slug") or not a.get("title"):
            critical.append("article missing slug or title")
        if a.get("content_md") is not None and len(a.get("content_md", "")) < 80:
            warns.append(f"article '{a.get('slug')}' content_md too short")

    # SEO
    seo = payload.get("seo") or {}
    if not seo.get("robots"):
        warns.append("seo.robots is empty")

    # Score
    score = 100 - 15 * len(critical) - 3 * len(warns)
    score = max(0, min(100, score))
    return critical, warns, score


_REFINEMENT_PROMPT = """You are the SitePayload Refinement Agent.

You receive:
- the previous site_payload JSON
- a QA report listing critical_issues and warnings

Your job: return a CORRECTED site_payload that fixes ALL critical_issues and as many
warnings as possible, WITHOUT regressing what was correct. Keep the same overall
structure, ids, palette and tone. Output VALID JSON only (the full corrected
SitePayload), no commentary, no markdown.

Conform exactly to the SitePayload contract:
- page_schema.pages[].meta {slug,title(10–80),description(50–180),og,schema_org}
- page_schema.pages[].layout {header_id,footer_id}
- page_schema.pages[].sections[] with id, type in [hero.split, hero.center,
  features.grid, about.split, testimonials.carousel, pricing.table, faq.accordion,
  cta.banner, form.contact, blog.index, richtext, gallery.grid] and required props.
- design_tokens.palette colors must be #RRGGBB.
- form.id consistent with any form.contact section's form_id.
- No placeholder text (lorem ipsum, "à compléter", etc.).
"""


def _normalize_payload(payload: dict[str, Any], brief: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    fb = _astro_fallback(brief)

    if not isinstance(payload, dict):
        warnings.append("payload not a dict; replaced by fallback")
        return fb, warnings

    ps = payload.get("page_schema") if isinstance(payload.get("page_schema"), dict) else {}
    pages = ps.get("pages") if isinstance(ps.get("pages"), list) else []
    if not pages:
        warnings.append("no pages; using fallback pages")
        pages = fb["page_schema"]["pages"]

    cleaned_pages = []
    used_ids: set[str] = set()
    for i, p in enumerate(pages):
        if not isinstance(p, dict):
            continue
        meta = p.get("meta") if isinstance(p.get("meta"), dict) else {}
        meta.setdefault("slug", "home" if i == 0 else f"page-{i}")
        meta.setdefault("title", brief.get("business_name") or "Page")
        meta.setdefault("description", "")
        meta.setdefault("og", {})
        meta.setdefault("schema_org", {})
        layout = p.get("layout") if isinstance(p.get("layout"), dict) else {}
        layout.setdefault("header_id", "default")
        layout.setdefault("footer_id", "default")
        sections = p.get("sections") if isinstance(p.get("sections"), list) else []
        cleaned_sections = []
        for j, s in enumerate(sections):
            if not isinstance(s, dict):
                continue
            stype = s.get("type")
            if stype not in _ALLOWED_TYPES:
                warnings.append(f"page {meta['slug']} section {j}: unknown type '{stype}' skipped")
                continue
            sid = str(s.get("id") or f"{stype.replace('.', '-')}-{j}")
            base = sid
            k = 1
            while sid in used_ids:
                sid = f"{base}-{k}"
                k += 1
            used_ids.add(sid)
            props = s.get("props") if isinstance(s.get("props"), dict) else {}
            cleaned_sections.append({"id": sid, "type": stype, "props": props})
        if not cleaned_sections:
            warnings.append(f"page {meta['slug']}: no valid sections; using fallback")
            cleaned_sections = fb["page_schema"]["pages"][0]["sections"]
        cleaned_pages.append({"meta": meta, "layout": layout, "sections": cleaned_sections})

    out = {
        "page_schema": {"pages": cleaned_pages},
        "design_tokens": payload.get("design_tokens") if isinstance(payload.get("design_tokens"), dict) else fb["design_tokens"],
        "seo": payload.get("seo") if isinstance(payload.get("seo"), dict) else fb["seo"],
        "form": payload.get("form") if isinstance(payload.get("form"), dict) else fb["form"],
        "analytics": payload.get("analytics") if isinstance(payload.get("analytics"), dict) else fb["analytics"],
        "articles": payload.get("articles") if isinstance(payload.get("articles"), list) else [],
    }
    return out, warnings


def _payload_to_sections(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt payload to the legacy `Project.sections` shape used by the editor."""
    out: list[dict[str, Any]] = []
    pages = payload.get("page_schema", {}).get("pages", [])
    if not pages:
        return out
    home = pages[0]
    for s in home.get("sections", []):
        props = s.get("props", {})
        title = props.get("title") or s.get("type", "")
        content = props.get("subtitle") or props.get("body") or props.get("markdown") or ""
        out.append({"id": s.get("id"), "title": str(title), "content": str(content), "enabled": True, "type": s.get("type")})
    return out


# ----- Pipeline -----

def generate_astro_site_payload(
    brief: dict[str, Any],
    on_progress: ProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    def _emit(step: str, status: str, progress: int, label: str, **extra: Any) -> None:
        if on_progress is None:
            return
        ev = {"step": step, "status": status, "progress": progress, "label": label, "ts": datetime.utcnow().isoformat()}
        ev.update(extra)
        try:
            on_progress(ev)
        except Exception:
            pass

    _emit("astro_start", "running", 5, "Mode Astro : génération du site.json")

    if not settings.deepseek_api_key:
        _emit("fallback", "running", 30, "Mode local (sans clé DeepSeek)")
        payload = _astro_fallback(brief)
        warnings: list[str] = ["Generated locally (no DeepSeek key)."]
        agents = [{
            "id": "agent-astro-fallback", "name": "astro_fallback",
            "status": "ok", "duration_ms": 0, "tokens_in": 0, "tokens_out": 0, "output": payload,
        }]
        files = [{"path": "content/site.json", "content": json.dumps(payload, ensure_ascii=False, indent=2)}]
        sections = _payload_to_sections(payload)
        output = {
            "render_mode": "astro",
            "site_payload": payload,
            "design_tokens": payload["design_tokens"],
            "warnings": warnings,
            "qa_report": {"score": 70, "warnings": warnings, "critical_issues": []},
        }
        _emit("done", "ok", 100, "Site Astro généré (fallback)", files=len(files))
        return agents, output, sections, files

    agents: list[dict[str, Any]] = []

    # 1. Architect — initial draft
    _emit("astro_payload", "running", 20, "Site Architect : production du SitePayload")
    architect = _agent_call("agent-astro-architect", "astro_architect", _ASTRO_PROMPT, {"brief": brief})
    agents.append(architect)
    _emit("astro_payload", architect["status"], 50, f"Site Architect terminé ({architect['status']})")

    raw = architect["output"] if architect["status"] == "ok" else {}
    payload, norm_warnings = _normalize_payload(raw, brief)

    # 2. QA — validate & score
    _emit("astro_qa", "running", 60, "QA : validation stricte du SitePayload")
    critical, warns, score = _validate_payload(payload)
    warns = list(dict.fromkeys(norm_warnings + warns))  # dedup, preserve order
    _emit("astro_qa", "ok", 70, f"QA : score={score}, critical={len(critical)}, warnings={len(warns)}",
          score=score, critical=len(critical), warnings=len(warns))

    # 3. Refinement — only when score is poor or critical issues exist
    refined = False
    if (critical or score < 75) and settings.deepseek_api_key:
        _emit("astro_refine", "running", 80, "Refinement : correction d'après le rapport QA")
        refinement = _agent_call(
            "agent-astro-refinement",
            "astro_refinement",
            _REFINEMENT_PROMPT,
            {"site_payload": payload, "qa_report": {"critical_issues": critical, "warnings": warns, "score": score}},
        )
        agents.append(refinement)
        if refinement["status"] == "ok" and isinstance(refinement.get("output"), dict):
            refined_payload, refine_norm_warns = _normalize_payload(refinement["output"], brief)
            new_critical, new_warns, new_score = _validate_payload(refined_payload)
            if new_score >= score and len(new_critical) <= len(critical):
                payload, critical, warns, score = refined_payload, new_critical, new_warns, new_score
                warns = list(dict.fromkeys(refine_norm_warns + warns))
                refined = True
                _emit("astro_refine", "ok", 90, f"Refinement appliqué (score={score})", score=score)
            else:
                _emit("astro_refine", "ok", 90, "Refinement ignoré (régression)", score=score)
        else:
            _emit("astro_refine", "failed", 90, "Refinement échoué, payload initial conservé")

    files = [{"path": "content/site.json", "content": json.dumps(payload, ensure_ascii=False, indent=2)}]
    sections = _payload_to_sections(payload)
    output = {
        "render_mode": "astro",
        "site_payload": payload,
        "design_tokens": payload["design_tokens"],
        "warnings": warns,
        "qa_report": {
            "score": score,
            "critical_issues": critical,
            "warnings": warns,
            "refined": refined,
        },
    }
    _emit("done", "ok", 100, f"Site Astro généré (score={score})",
          files=len(files), score=score, refined=refined)
    return agents, output, sections, files
