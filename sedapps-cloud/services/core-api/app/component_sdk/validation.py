from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.component_sdk.models import ComponentInstance, PageDocument, PropDefinition
from app.component_sdk.registry import component_registry, get_manifest


def _valid_prop(value: Any, definition: PropDefinition) -> bool:
    if value is None:
        return not definition.required
    if definition.type in {"string", "url", "enum"} and not isinstance(value, str):
        return False
    if definition.type == "boolean" and not isinstance(value, bool):
        return False
    if definition.type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        return False
    if definition.type == "object" and not isinstance(value, dict):
        return False
    if definition.type == "array" and not isinstance(value, list):
        return False
    if definition.type == "enum" and value not in definition.values:
        return False
    if definition.type == "url" and value and urlparse(value).scheme not in {"http", "https", "mailto", "tel", ""}:
        return False
    if definition.type == "number":
        if definition.minimum is not None and value < definition.minimum:
            return False
        if definition.maximum is not None and value > definition.maximum:
            return False
    return True


def _validate_instance(instance: ComponentInstance, path: str, ids: set[str], errors: list[str]) -> None:
    if instance.id in ids:
        errors.append(f"{path}: duplicate id '{instance.id}'")
    ids.add(instance.id)
    if instance.type not in component_registry:
        errors.append(f"{path}: unknown component '{instance.type}'")
        return

    manifest = get_manifest(instance.type)
    unknown_props = set(instance.props) - set(manifest.props)
    if unknown_props:
        errors.append(f"{path}: unsupported props {sorted(unknown_props)}")
    for name, definition in manifest.props.items():
        value = instance.props.get(name, definition.default)
        if not _valid_prop(value, definition):
            errors.append(f"{path}.props.{name}: invalid {definition.type}")

    unknown_slots = set(instance.slots) - set(manifest.slots)
    if unknown_slots:
        errors.append(f"{path}: unsupported slots {sorted(unknown_slots)}")
    for slot_name, children in instance.slots.items():
        slot = manifest.slots.get(slot_name)
        if not slot:
            continue
        if len(children) < slot.minimum or (slot.maximum is not None and len(children) > slot.maximum):
            errors.append(f"{path}.slots.{slot_name}: invalid child count")
        for index, child in enumerate(children):
            if "*" not in slot.accepts and child.type not in slot.accepts:
                errors.append(f"{path}.slots.{slot_name}[{index}]: '{child.type}' not accepted")
            _validate_instance(child, f"{path}.slots.{slot_name}[{index}]", ids, errors)


def validate_document(raw: dict[str, Any] | PageDocument) -> PageDocument:
    document = raw if isinstance(raw, PageDocument) else PageDocument.model_validate(raw)
    errors: list[str] = []
    ids: set[str] = set()
    for index, page in enumerate(document.pages):
        _validate_instance(page, f"pages[{index}]", ids, errors)
    if errors:
        raise ValueError("; ".join(errors))
    return document
