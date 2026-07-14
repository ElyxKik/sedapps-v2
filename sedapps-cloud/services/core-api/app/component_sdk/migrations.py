from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any


def _safe_id(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return normalized or fallback


def _string_values(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if isinstance(item, str)}


def _text_node(node_id: str, text: str, node_type: str = "Text") -> dict[str, Any]:
    props = {"text": text}
    if node_type == "Title":
        props["level"] = "h2"
    return {"id": node_id, "type": node_type, "props": props, "styles": {}, "slots": {}}


def _legacy_section(section: dict[str, Any], index: int) -> dict[str, Any]:
    section_id = _safe_id(str(section.get("id") or section.get("type") or f"section-{index}"), f"section-{index}")
    children: list[dict[str, Any]] = []
    title = section.get("title") or section.get("headline") or section.get("heading")
    body = section.get("description") or section.get("content") or section.get("body")
    if title:
        children.append(_text_node(f"{section_id}-title", str(title), "Title"))
    if body:
        children.append(_text_node(f"{section_id}-text", str(body)))
    for item_index, item in enumerate(section.get("items") or []):
        if not isinstance(item, dict):
            continue
        card_id = f"{section_id}-card-{item_index}"
        card_children = []
        if item.get("title") or item.get("label"):
            card_children.append(_text_node(f"{card_id}-title", str(item.get("title") or item.get("label")), "Title"))
        if item.get("description") or item.get("content"):
            card_children.append(_text_node(f"{card_id}-text", str(item.get("description") or item.get("content"))))
        children.append({"id": card_id, "type": "Card", "props": {}, "styles": {}, "slots": {"body": card_children}})
    return {
        "id": section_id,
        "type": "Section",
        "props": {"variant": "hero" if index == 0 else "default"},
        "styles": {},
        "slots": {"content": children},
    }


class _ClassicHtmlParser(HTMLParser):
    """Extract editable semantic content from legacy generated HTML."""

    editable_tags = {"h1": "Title", "h2": "Title", "h3": "Title", "p": "Text", "a": "Button"}

    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[dict[str, Any]] = []
        self._current: dict[str, Any] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._current is not None or tag not in self.editable_tags:
            return
        values = {key: value or "" for key, value in attrs}
        self._current = {"tag": tag, "attrs": values}
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current is None or self._current["tag"] != tag:
            return
        text = re.sub(r"\s+", " ", "".join(self._text)).strip()
        if text:
            index = len(self.nodes)
            kind = self.editable_tags[tag]
            props: dict[str, Any] = {} if kind == "Button" else {"text": text}
            if kind == "Title":
                props["level"] = tag
            if kind == "Button":
                props["label"] = text
                props["href"] = self._current["attrs"].get("href") or "#"
            self.nodes.append({
                "id": f"legacy-{tag}-{index}",
                "type": kind,
                "props": props,
                "styles": {},
                "slots": {},
            })
        self._current = None
        self._text = []


def _classic_html_sections(page_schema: dict[str, Any]) -> list[dict[str, Any]]:
    files = page_schema.get("generated_files") or page_schema.get("files") or []
    index_html = next(
        (str(item.get("content") or "") for item in files if item.get("path") == "index.html"),
        "",
    )
    if not index_html:
        return []
    parser = _ClassicHtmlParser()
    parser.feed(index_html)
    if not parser.nodes:
        return []
    return [{
        "id": "legacy-content",
        "type": "Section",
        "props": {"variant": "default"},
        "styles": {},
        "slots": {"content": parser.nodes},
    }]


def migrate_page_schema(page_schema: dict[str, Any], design_tokens: dict[str, Any] | None = None) -> dict[str, Any]:
    if page_schema.get("schema_version") and page_schema.get("type") == "Website":
        return page_schema
    pages = page_schema.get("pages") if isinstance(page_schema.get("pages"), list) else []
    legacy_page = pages[0] if pages and isinstance(pages[0], dict) else {}
    sections = legacy_page.get("sections") or page_schema.get("sections") or []
    page_id = _safe_id(str(legacy_page.get("id") or legacy_page.get("slug") or "home"), "home")
    tokens = design_tokens or {}
    palette = tokens.get("palette") if isinstance(tokens.get("palette"), dict) else tokens
    colors = {
        "primary": "#6366f1",
        "secondary": "#22d3ee",
        "accent": "#f97316",
        "bg": "#0f1117",
        "surface": "#161b27",
        "text": "#f8fafc",
        "muted": "#94a3b8",
    }
    colors.update({key: str(value) for key, value in palette.items() if isinstance(value, str)})
    return {
        "schema_version": "1.0.0",
        "type": "Website",
        "design_system": {
            "version": "1.0.0",
            "dna": tokens.get("dna", {}),
            "colors": colors,
            "typography": _string_values(tokens.get("typography")),
            "spacing": {"md": "24px", "lg": "48px", **_string_values(tokens.get("spacing"))},
            "radius": {"medium": "16px", **_string_values(tokens.get("radius"))},
            "shadows": _string_values(tokens.get("shadows")),
            "animations": _string_values(tokens.get("animations")),
        },
        "pages": [{
            "id": page_id,
            "type": "Page",
            "props": {"slug": str(legacy_page.get("slug") or "home")},
            "styles": {},
            "slots": {"body": (
                [_legacy_section(item, index) for index, item in enumerate(sections) if isinstance(item, dict)]
                or _classic_html_sections(page_schema)
            )},
        }],
        "legacy": {key: page_schema[key] for key in ("render_mode", "generated_files", "form", "analytics", "articles") if key in page_schema},
    }
