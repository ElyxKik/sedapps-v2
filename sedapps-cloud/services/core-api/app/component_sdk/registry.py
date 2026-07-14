from __future__ import annotations

from app.component_sdk.models import ComponentManifest, PropDefinition, SlotDefinition


COMMON_ACTIONS = ["duplicate", "delete", "rename", "animate", "replace"]


def _manifest(name: str, category: str, icon: str, *, props=None, slots=None, droppable=False):
    return ComponentManifest(
        name=name,
        category=category,
        icon=icon,
        props=props or {},
        slots=slots or {},
        droppable=droppable,
        actions=COMMON_ACTIONS,
        ai_prompt=f"Tu modifies uniquement le composant {name}. Respecte le Design System.",
    )


component_registry: dict[str, ComponentManifest] = {
    "Page": _manifest(
        "Page", "Structure", "page", droppable=True,
        props={"slug": PropDefinition(type="string", required=True)},
        slots={"body": SlotDefinition(accepts=["Section", "Header", "Footer"], minimum=1)},
    ),
    "Section": _manifest(
        "Section", "Layout", "section", droppable=True,
        props={"variant": PropDefinition(type="enum", default="default", values=["default", "hero", "split", "grid"])},
        slots={"content": SlotDefinition(accepts=["*"])},
    ),
    "Header": _manifest("Header", "Navigation", "header", droppable=True, slots={"content": SlotDefinition(accepts=["Logo", "Menu", "Button"])}),
    "Footer": _manifest("Footer", "Navigation", "footer", droppable=True, slots={"content": SlotDefinition(accepts=["Text", "Menu", "Button", "Logo"])}),
    "Title": _manifest("Title", "Typography", "title", props={"text": PropDefinition(type="string", required=True), "level": PropDefinition(type="enum", default="h2", values=["h1", "h2", "h3"])}),
    "Text": _manifest("Text", "Typography", "text", props={"text": PropDefinition(type="string", required=True)}),
    "Button": _manifest(
        "Button", "Basic", "button",
        props={
            "label": PropDefinition(type="string", required=True),
            "variant": PropDefinition(type="enum", default="primary", values=["primary", "secondary", "ghost", "outline", "danger", "success", "link"]),
            "href": PropDefinition(type="url"),
            "disabled": PropDefinition(type="boolean", default=False),
        },
    ),
    "Image": _manifest("Image", "Media", "image", props={"src": PropDefinition(type="url", required=True), "alt": PropDefinition(type="string", required=True)}),
    "Logo": _manifest("Logo", "Brand", "logo", props={"src": PropDefinition(type="url"), "label": PropDefinition(type="string")}),
    "Menu": _manifest("Menu", "Navigation", "menu", props={"items": PropDefinition(type="array", default=[])}),
    "Card": _manifest("Card", "Layout", "card", droppable=True, slots={"header": SlotDefinition(), "body": SlotDefinition(), "footer": SlotDefinition()}),
}


def get_manifest(component_type: str) -> ComponentManifest:
    try:
        return component_registry[component_type]
    except KeyError as exc:
        raise ValueError(f"unknown component type: {component_type}") from exc
