from __future__ import annotations

from typing import Any

from app.component_sdk.models import ComponentInstance, PageDocument
from app.component_sdk.registry import get_manifest


def _find(nodes: list[ComponentInstance], component_id: str, parent: ComponentInstance | None = None):
    for node in nodes:
        if node.id == component_id:
            return node, parent
        for children in node.slots.values():
            found = _find(children, component_id, node)
            if found:
                return found
    return None


def build_component_ai_context(raw: dict[str, Any], component_id: str) -> dict[str, Any]:
    document = PageDocument.model_validate(raw)
    found = _find(document.pages, component_id)
    if not found:
        raise ValueError(f"component not found: {component_id}")
    component, parent = found
    manifest = get_manifest(component.type)
    return {
        "instruction": manifest.ai_prompt,
        "scope": {"component_id": component.id, "allowed_path": f"component:{component.id}"},
        "component": component.model_dump(),
        "schema": manifest.model_dump(),
        "parent": {"id": parent.id, "type": parent.type} if parent else None,
        "children": [{"id": child.id, "type": child.type} for values in component.slots.values() for child in values],
        "design_system": document.design_system.model_dump(),
        "constraints": ["Ne modifie aucun autre composant.", "Utilise uniquement les design tokens.", "Retourne des opérations JSON structurées."],
    }
