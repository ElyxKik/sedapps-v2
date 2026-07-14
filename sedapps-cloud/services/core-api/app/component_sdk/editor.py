from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.component_sdk.models import ComponentInstance, PageDocument
from app.component_sdk.registry import get_manifest
from app.component_sdk.validation import validate_document


def _walk(nodes: list[ComponentInstance]):
    for node in nodes:
        yield node
        for children in node.slots.values():
            yield from _walk(children)


def _selected(document: PageDocument, component_id: str) -> ComponentInstance:
    for component in _walk(document.pages):
        if component.id == component_id:
            return component
    raise ValueError(f"component not found: {component_id}")


def _text_prop(component: ComponentInstance) -> str:
    manifest = get_manifest(component.type)
    for candidate in ("text", "label", "alt"):
        if candidate in manifest.props:
            return candidate
    raise ValueError(f"component '{component.type}' has no editable text property")


def _token_exists(document: PageDocument, token: str) -> bool:
    if not token.startswith("theme."):
        return False
    value: Any = document.design_system.model_dump()
    for part in token.split(".")[1:]:
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return isinstance(value, str)


def apply_component_ops(
    raw: dict[str, Any], component_id: str, ops: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    document = PageDocument.model_validate(deepcopy(raw))
    component = _selected(document, component_id)
    manifest = get_manifest(component.type)
    applied: list[dict[str, Any]] = []

    for operation in ops:
        op = operation.get("op")
        if op == "set_text":
            name, value = _text_prop(component), operation.get("value")
        elif op in {"set_prop", "set_attr"}:
            name = operation.get("path") or operation.get("name")
            value = operation.get("value")
        elif op == "unset_prop":
            name = operation.get("path") or operation.get("name")
            if name not in manifest.props:
                raise ValueError(f"unsupported prop '{name}' for {component.type}")
            if manifest.props[name].required:
                raise ValueError(f"required prop '{name}' cannot be removed")
            component.props.pop(name, None)
            applied.append({"op": op, "path": name})
            continue
        elif op in {"set_style_token", "set_style"}:
            name = operation.get("path") or operation.get("name")
            token = operation.get("token") or operation.get("value")
            if not isinstance(name, str) or not isinstance(token, str):
                raise ValueError("style name and token are required")
            if not _token_exists(document, token):
                raise ValueError(f"unknown or unsafe design token '{token}'")
            component.styles[name] = token
            applied.append({"op": "set_style_token", "path": name, "token": token})
            continue
        else:
            raise ValueError(f"unsupported operation: {op}")

        if not isinstance(name, str) or name not in manifest.props:
            raise ValueError(f"unsupported prop '{name}' for {component.type}")
        component.props[name] = value
        applied.append({"op": "set_prop", "path": name, "value": value})

    component.history.append({"operations": applied})
    result = document.model_dump()
    validate_document(result)
    return result, {
        "id": component.id,
        "type": component.type,
        "props": component.props,
        "styles": component.styles,
    }
