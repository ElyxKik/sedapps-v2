from __future__ import annotations

import html

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.models.site_version import SiteVersion

router = APIRouter()


def _latest_site_version(db: Session, slug: str) -> tuple[Project, SiteVersion]:
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="preview not found")
    version = (
        db.query(SiteVersion)
        .filter(SiteVersion.project_id == project.id)
        .order_by(SiteVersion.version.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="site version not found")
    return project, version


def _palette(tokens: dict) -> dict[str, str]:
    raw = tokens.get("palette") if isinstance(tokens.get("palette"), dict) else tokens
    return {
        "primary": str(raw.get("primary") or "#6366F1"),
        "secondary": str(raw.get("secondary") or "#8B5CF6"),
        "accent": str(raw.get("accent") or "#22D3EE"),
        "bg": str(raw.get("bg") or "#0F1117"),
        "surface": str(raw.get("surface") or "#161B27"),
        "text": str(raw.get("text") or "#F8FAFC"),
        "muted": str(raw.get("muted") or "#94A3B8"),
    }


def _page_items(page_schema: dict) -> list[dict]:
    pages = page_schema.get("pages") if isinstance(page_schema, dict) else None
    if isinstance(pages, list) and pages:
        first = pages[0] if isinstance(pages[0], dict) else {}
        sections = first.get("sections") if isinstance(first.get("sections"), list) else []
        return [item for item in sections if isinstance(item, dict)]
    if isinstance(page_schema.get("sections"), list):
        return [item for item in page_schema["sections"] if isinstance(item, dict)]
    return []


def _section_html(section: dict, index: int) -> str:
    kind = html.escape(str(section.get("type") or section.get("kind") or "section"))
    title = html.escape(
        str(
            section.get("title")
            or section.get("headline")
            or section.get("heading")
            or kind.title()
        )
    )
    body = html.escape(
        str(section.get("content") or section.get("body") or section.get("description") or "")
    )
    items = section.get("items") if isinstance(section.get("items"), list) else []
    cards = "".join(
        f'<article class="card"><h3>{html.escape(str((item or {}).get("title") or (item or {}).get("label") or "Élément"))}</h3><p>{html.escape(str((item or {}).get("description") or (item or {}).get("content") or ""))}</p></article>'
        for item in items
        if isinstance(item, dict)
    )
    eyebrow = "Accueil" if index == 0 else kind.replace(".", " /")
    return f"""
<section class="section {'hero' if index == 0 else ''}" id="section-{index}">
  <div class="eyebrow">{html.escape(eyebrow)}</div>
  <h2>{title}</h2>
  <p>{body}</p>
  <div class="grid">{cards}</div>
</section>
"""


def _render_html(project: Project, version: SiteVersion) -> str:
    tokens = version.design_tokens or {}
    colors = _palette(tokens)
    typography = tokens.get("typography") if isinstance(tokens.get("typography"), dict) else {}
    heading_font = html.escape(
        str(typography.get("heading") or tokens.get("font_heading") or "Inter")
    )
    body_font = html.escape(str(typography.get("body") or tokens.get("font_body") or "Inter"))
    sections = _page_items(version.page_schema or {})
    if not sections:
        sections = [{"title": project.name, "description": "Votre site est prêt."}]
    content = "".join(_section_html(section, index) for index, section in enumerate(sections))
    title = html.escape(str((version.seo or {}).get("title") or project.name))
    description = html.escape(str((version.seo or {}).get("description") or project.sector or ""))
    nav = "".join(
        f'<a href="#section-{index}">{html.escape(str(section.get("title") or section.get("type") or index + 1))}</a>'
        for index, section in enumerate(sections[:5])
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family={heading_font.replace(' ', '+')}:wght@600;700;800&family={body_font.replace(' ', '+')}:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{ color-scheme: dark; --primary:{colors['primary']}; --secondary:{colors['secondary']}; --accent:{colors['accent']}; --bg:{colors['bg']}; --surface:{colors['surface']}; --text:{colors['text']}; --muted:{colors['muted']}; }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin:0; font-family:'{body_font}', system-ui, sans-serif; background: radial-gradient(circle at top left, color-mix(in srgb, var(--primary) 24%, transparent), transparent 34rem), var(--bg); color:var(--text); }}
    header {{ position:sticky; top:0; z-index:10; display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:1rem clamp(1rem, 4vw, 4rem); backdrop-filter:blur(18px); background:color-mix(in srgb, var(--bg) 78%, transparent); border-bottom:1px solid color-mix(in srgb, var(--text) 10%, transparent); }}
    .brand {{ font-weight:800; letter-spacing:-.04em; }}
    nav {{ display:flex; gap:1rem; flex-wrap:wrap; }}
    nav a {{ color:var(--muted); text-decoration:none; font-size:.92rem; }}
    nav a:hover {{ color:var(--text); }}
    main {{ width:min(1120px, calc(100% - 2rem)); margin:auto; }}
    .section {{ padding:clamp(4rem, 9vw, 7rem) 0; border-bottom:1px solid color-mix(in srgb, var(--text) 8%, transparent); }}
    .hero {{ min-height:72vh; display:grid; align-content:center; }}
    .eyebrow {{ color:var(--accent); text-transform:uppercase; letter-spacing:.18em; font-size:.78rem; font-weight:800; margin-bottom:1rem; }}
    h1, h2 {{ font-family:'{heading_font}', system-ui, sans-serif; font-size:clamp(2.6rem, 7vw, 6rem); line-height:.92; letter-spacing:-.075em; margin:0 0 1.2rem; max-width:920px; }}
    h3 {{ margin:.2rem 0 .6rem; }}
    p {{ color:var(--muted); font-size:clamp(1rem, 2vw, 1.22rem); line-height:1.75; max-width:760px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:1rem; margin-top:2rem; }}
    .card {{ border:1px solid color-mix(in srgb, var(--text) 10%, transparent); background:linear-gradient(180deg, color-mix(in srgb, var(--surface) 92%, white 8%), var(--surface)); border-radius:24px; padding:1.25rem; box-shadow:0 24px 80px rgba(0,0,0,.22); }}
    footer {{ padding:2rem clamp(1rem, 4vw, 4rem); color:var(--muted); display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; }}
    @media (max-width:720px) {{ header {{ align-items:flex-start; flex-direction:column; }} nav {{ font-size:.85rem; }} }}
  </style>
</head>
<body>
  <header><div class="brand">{html.escape(project.name)}</div><nav>{nav}</nav></header>
  <main>{content}</main>
  <footer><span>{html.escape(project.name)}</span><span>Site généré par SedApps</span></footer>
</body>
</html>"""


@router.get("/p/{slug}/", include_in_schema=False)
@router.get("/p/{slug}/index.html", tags=["preview"])
def preview_index(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    project, version = _latest_site_version(db, slug)
    page_schema = version.page_schema or {}
    
    if page_schema.get("render_mode") == "static_classic":
        files = page_schema.get("generated_files") or page_schema.get("files") or []
        for f in files:
            if f.get("path") == "index.html":
                return HTMLResponse(content=f.get("content") or "", status_code=200)
        raise HTTPException(status_code=404, detail="index.html not found in site files")
        
    return HTMLResponse(content=_render_html(project, version), status_code=200)


@router.get("/p/{slug}/{filename}", tags=["preview"])
def preview_asset(slug: str, filename: str, db: Session = Depends(get_db)) -> Response:
    project, version = _latest_site_version(db, slug)
    page_schema = version.page_schema or {}
    
    if page_schema.get("render_mode") == "static_classic":
        files = page_schema.get("generated_files") or page_schema.get("files") or []
        for f in files:
            if f.get("path") == filename:
                content = f.get("content") or ""
                media_type = "text/plain"
                if filename.endswith(".html"):
                    media_type = "text/html"
                elif filename.endswith(".css"):
                    media_type = "text/css"
                elif filename.endswith(".js"):
                    media_type = "application/javascript"
                elif filename.endswith(".svg"):
                    media_type = "image/svg+xml"
                elif filename.endswith(".png"):
                    media_type = "image/png"
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    media_type = "image/jpeg"
                elif filename.endswith(".json"):
                    media_type = "application/json"
                return Response(content=content, media_type=media_type)
        raise HTTPException(status_code=404, detail=f"file '{filename}' not found in static files")
        
    if filename == "styles.css":
        return Response(content="", media_type="text/css")
    if filename == "script.js":
        return Response(content="", media_type="application/javascript")
    raise HTTPException(status_code=404, detail="asset not found")
