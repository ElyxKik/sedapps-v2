"""HTML editor backend: annotate elements with stable IDs, inject overlay script,
and apply targeted ops (set_text, set_attr, set_style) for Elementor-like editing."""
from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, NavigableString

EDITABLE_TAGS = {
    "section", "header", "footer", "nav", "main", "article", "aside",
    "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "span", "a", "button",
    "img", "form", "input", "textarea", "select", "label",
    "ul", "ol", "li",
    "figure", "figcaption", "blockquote",
}

SKIP_TAGS = {"script", "style", "meta", "link", "title", "head", "html", "body"}


def _annotate(soup: BeautifulSoup) -> None:
    counter = 0
    for el in soup.find_all(True):
        if el.name in SKIP_TAGS:
            continue
        if el.name not in EDITABLE_TAGS:
            continue
        if el.has_attr("data-sed-id"):
            continue
        counter += 1
        el["data-sed-id"] = f"sed-{counter}"


_OVERLAY_CSS = """
[data-sed-hover]{outline:2px solid #38bdf8!important;outline-offset:-2px;cursor:pointer}
[data-sed-selected]{outline:2px solid #7c3aed!important;outline-offset:-2px;box-shadow:0 0 0 4px rgba(124,58,237,.18)!important}
html,body{cursor:default}
"""

_OVERLAY_JS = r"""
(function(){
  if (window.__sedEditor) return; window.__sedEditor = true;
  var hovered=null, selected=null;
  document.addEventListener('mouseover', function(e){
    var el = e.target.closest && e.target.closest('[data-sed-id]');
    if (!el || el === hovered) return;
    if (hovered) hovered.removeAttribute('data-sed-hover');
    hovered = el; el.setAttribute('data-sed-hover','');
  }, true);
  document.addEventListener('mouseout', function(){
    if (hovered) { hovered.removeAttribute('data-sed-hover'); hovered=null; }
  }, true);
  document.addEventListener('click', function(e){
    var el = e.target.closest && e.target.closest('[data-sed-id]');
    if (!el) return;
    e.preventDefault(); e.stopPropagation();
    if (selected) selected.removeAttribute('data-sed-selected');
    selected = el; el.setAttribute('data-sed-selected','');
    var cs = getComputedStyle(el);
    var info = {
      type: 'sed:select',
      id: el.getAttribute('data-sed-id'),
      tag: el.tagName.toLowerCase(),
      text: (el.innerText||'').slice(0,800),
      src: el.getAttribute('src')||null,
      href: el.getAttribute('href')||null,
      alt: el.getAttribute('alt')||null,
      bg: cs.backgroundColor,
      color: cs.color,
      classes: el.className||''
    };
    parent && parent.postMessage(info, '*');
  }, true);
  document.addEventListener('submit', function(e){ e.preventDefault(); }, true);
  window.addEventListener('message', function(ev){
    var data = ev.data || {};
    if (data.type !== 'sed:apply') return;
    var el = document.querySelector('[data-sed-id="'+data.id+'"]');
    if (!el) return;
    (data.ops||[]).forEach(function(op){
      if (op.op === 'set_text') el.textContent = op.value;
      else if (op.op === 'set_attr') el.setAttribute(op.name, op.value);
      else if (op.op === 'set_style') el.style[op.name] = op.value;
    });
    parent && parent.postMessage({type:'sed:applied', id:data.id}, '*');
  });
  // signal ready
  setTimeout(function(){ parent && parent.postMessage({type:'sed:ready'}, '*'); }, 50);
})();
"""


def prepare_editable_html(html_str: str) -> str:
    """Return the HTML with stable data-sed-id attributes and the editor overlay injected."""
    soup = BeautifulSoup(html_str or "", "html.parser")
    _annotate(soup)
    # ensure head/body
    head = soup.find("head")
    body = soup.find("body")
    if head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)
    style_tag = soup.new_tag("style")
    style_tag.string = _OVERLAY_CSS
    head.append(style_tag)
    target = body if body is not None else soup
    script_tag = soup.new_tag("script")
    script_tag.string = _OVERLAY_JS
    target.append(script_tag)
    return str(soup)


def annotate_only(html_str: str) -> str:
    """Return HTML with stable data-sed-id but without overlay (for persistence)."""
    soup = BeautifulSoup(html_str or "", "html.parser")
    _annotate(soup)
    return str(soup)


def apply_ops(html_str: str, element_id: str, ops: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """Apply ops to element identified by data-sed-id. Returns (new_html, element_summary)."""
    soup = BeautifulSoup(html_str or "", "html.parser")
    _annotate(soup)  # make sure ids exist
    el = soup.find(attrs={"data-sed-id": element_id})
    if el is None:
        raise KeyError(f"element {element_id} not found")
    for op in ops or []:
        kind = op.get("op")
        if kind == "set_text":
            value = str(op.get("value", ""))
            # replace children with single text node
            el.clear()
            el.append(NavigableString(value))
        elif kind == "set_attr":
            name = op.get("name")
            value = op.get("value", "")
            if not name:
                continue
            if value is None or value == "":
                if el.has_attr(name):
                    del el[name]
            else:
                el[name] = str(value)
        elif kind == "set_style":
            name = op.get("name")
            value = op.get("value", "")
            if not name:
                continue
            current = el.get("style", "") or ""
            decls = [d.strip() for d in current.split(";") if d.strip()]
            kept = [d for d in decls if not d.lower().startswith(name.lower() + ":")]
            if value not in (None, ""):
                kept.append(f"{name}: {value}")
            el["style"] = "; ".join(kept)
        elif kind == "add_class":
            classes = (el.get("class") or [])
            cls = str(op.get("value", "")).strip()
            if cls and cls not in classes:
                classes.append(cls)
            el["class"] = classes
        elif kind == "remove_class":
            classes = el.get("class") or []
            cls = str(op.get("value", "")).strip()
            el["class"] = [c for c in classes if c != cls]
    summary = {
        "id": element_id,
        "tag": el.name,
        "text": el.get_text()[:500],
        "outer_html": str(el)[:2000],
    }
    return str(soup), summary
