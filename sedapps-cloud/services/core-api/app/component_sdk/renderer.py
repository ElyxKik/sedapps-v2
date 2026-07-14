from __future__ import annotations

import html
import re
from typing import Any

from app.component_sdk.models import ComponentInstance
from app.component_sdk.validation import validate_document


SAFE_STYLE_PROPERTIES = {
    "background",
    "backgroundColor",
    "borderColor",
    "borderRadius",
    "boxShadow",
    "color",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "gap",
    "margin",
    "marginBottom",
    "marginTop",
    "padding",
    "textAlign",
}


def _kebab(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", value).lower().replace("_", "-")


def _style(instance: ComponentInstance) -> str:
    declarations = []
    for name, token in instance.styles.items():
        if name not in SAFE_STYLE_PROPERTIES or not isinstance(token, str):
            continue
        variable = "--" + "-".join(_kebab(part) for part in token.split(".")[1:])
        declarations.append(f"{_kebab(name)}:var({variable})")
    return f' style="{html.escape(";".join(declarations), quote=True)}"' if declarations else ""


def _children(instance: ComponentInstance, slot: str | None = None) -> str:
    slots = [instance.slots.get(slot, [])] if slot else instance.slots.values()
    return "".join(_render(child) for children in slots for child in children)


def _render(instance: ComponentInstance) -> str:
    attrs = f'data-sed-id="{html.escape(instance.id, quote=True)}" data-sed-type="{html.escape(instance.type, quote=True)}"{_style(instance)}'
    props = instance.props
    kind = instance.type
    if kind == "Page":
        return f"<main {attrs}>{_children(instance, 'body')}</main>"
    if kind == "Section":
        variant = html.escape(str(props.get("variant", "default")), quote=True)
        return f'<section {attrs} class="sed-section sed-section--{variant}"><div class="sed-container">{_children(instance, "content")}</div></section>'
    if kind == "Header":
        return f'<header {attrs} class="sed-header"><div class="sed-container">{_children(instance, "content")}</div></header>'
    if kind == "Footer":
        return f'<footer {attrs} class="sed-footer"><div class="sed-container">{_children(instance, "content")}</div></footer>'
    if kind == "Title":
        level = props.get("level", "h2") if props.get("level") in {"h1", "h2", "h3"} else "h2"
        return f'<{level} {attrs}>{html.escape(str(props.get("text", "")))}</{level}>'
    if kind == "Text":
        return f'<p {attrs}>{html.escape(str(props.get("text", "")))}</p>'
    if kind == "Button":
        label = html.escape(str(props.get("label", "")))
        variant = html.escape(str(props.get("variant", "primary")), quote=True)
        href = html.escape(str(props.get("href") or "#"), quote=True)
        return f'<a {attrs} class="sed-button sed-button--{variant}" href="{href}">{label}</a>'
    if kind == "Image":
        src = html.escape(str(props.get("src", "")), quote=True)
        alt = html.escape(str(props.get("alt", "")), quote=True)
        return f'<img {attrs} src="{src}" alt="{alt}" loading="lazy">'
    if kind == "Logo":
        src = props.get("src")
        if src:
            return f'<img {attrs} class="sed-logo" src="{html.escape(str(src), quote=True)}" alt="{html.escape(str(props.get("label") or "Logo"), quote=True)}">'
        return f'<strong {attrs} class="sed-logo">{html.escape(str(props.get("label") or "Logo"))}</strong>'
    if kind == "Menu":
        links = "".join(
            f'<a href="{html.escape(str(item.get("href") or "#"), quote=True)}">{html.escape(str(item.get("label") or "Lien"))}</a>'
            for item in props.get("items", [])
            if isinstance(item, dict)
        )
        return f'<nav {attrs} class="sed-menu">{links}</nav>'
    if kind == "Card":
        return f'<article {attrs} class="sed-card">{_children(instance)}</article>'
    raise ValueError(f"renderer missing for component: {kind}")


def _variables(design_system: dict[str, Any]) -> str:
    declarations = []
    for group in ("colors", "typography", "spacing", "radius", "shadows", "animations"):
        for name, value in (design_system.get(group) or {}).items():
            if isinstance(value, str):
                declarations.append(f"--{_kebab(group)}-{_kebab(name)}:{value}")
    return ";".join(declarations)


def render_component_document(
    raw: dict[str, Any], title: str, description: str = "", edit_mode: bool = False,
    page_slug: str | None = None,
) -> str:
    document = validate_document(raw)
    pages = document.pages
    if page_slug:
        pages = [page for page in pages if page.props.get("slug") == page_slug] or pages[:1]
    content = "".join(_render(page) for page in pages)
    variables = _variables(document.design_system.model_dump())
    editor_script = ""
    if edit_mode:
        editor_script = """<script>
document.addEventListener('click', (event) => {
  const selected = event.target.closest('[data-sed-id]');
  if (!selected) return;
  event.preventDefault();
  event.stopPropagation();
  document.querySelectorAll('[data-sed-selected]').forEach((node) => node.removeAttribute('data-sed-selected'));
  selected.setAttribute('data-sed-selected', 'true');
  parent.postMessage({type:'sed:select', id:selected.dataset.sedId, componentType:selected.dataset.sedType, tag:selected.tagName.toLowerCase(), text:selected.textContent.trim(), href:selected.getAttribute('href') || '', src:selected.getAttribute('src') || '', alt:selected.getAttribute('alt') || '', classes:[...selected.classList]}, '*');
}, true);
window.addEventListener('message', (event) => {
  if (!event.data || event.data.type !== 'sed:apply') return;
  const selected = document.querySelector(`[data-sed-id="${CSS.escape(event.data.id)}"]`);
  if (!selected) return;
  for (const operation of event.data.ops || []) {
    if (operation.op === 'set_text') selected.textContent = operation.value ?? '';
    if ((operation.op === 'set_prop' || operation.op === 'set_attr') && ['href','src','alt'].includes(operation.path || operation.name)) selected.setAttribute(operation.path || operation.name, operation.value ?? '');
    if ((operation.op === 'set_style_token' || operation.op === 'set_style') && String(operation.token || operation.value || '').startsWith('theme.')) {
      const token = '--' + String(operation.token || operation.value).slice(6).replaceAll('.', '-');
      selected.style[operation.path || operation.name] = `var(${token})`;
    }
  }
});
</script>"""
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}">
<style>:root{{{variables}}}*{{box-sizing:border-box}}body{{margin:0;background:var(--colors-bg,#0f1117);color:var(--colors-text,#f8fafc);font-family:var(--typography-body,Inter),sans-serif}}.sed-container{{width:min(1120px,calc(100% - 2rem));margin:auto}}.sed-section{{padding:var(--spacing-xl,5rem) 0}}.sed-section--hero{{min-height:72vh;display:grid;align-items:center}}h1,h2,h3{{font-family:var(--typography-heading,Inter),sans-serif}}h1{{font-size:clamp(2.8rem,7vw,6rem)}}p{{color:var(--colors-muted,#94a3b8);line-height:1.7}}.sed-button{{display:inline-flex;padding:.8rem 1.2rem;border-radius:var(--radius-medium,1rem);text-decoration:none}}.sed-button--primary{{background:var(--colors-primary,#6366f1);color:white}}.sed-card{{padding:1.25rem;border-radius:var(--radius-large,1.5rem);background:var(--colors-surface,#161b27)}}.sed-header .sed-container,.sed-footer .sed-container,.sed-menu{{display:flex;align-items:center;justify-content:space-between;gap:1rem}}[data-sed-selected]{{outline:2px solid #22d3ee;outline-offset:4px}}</style></head><body>{content}{editor_script}</body></html>"""
