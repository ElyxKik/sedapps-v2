from __future__ import annotations

from typing import Any

from app.config import settings


class SubmissionValidationError(ValueError):
    pass


def normalize_submission(raw: dict[str, Any], schema: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    honeypot = schema.get("anti_spam", {}).get("honeypot") or settings.INBOX_HONEYPOT_FIELD
    is_spam = bool(str(raw.get(honeypot, "")).strip())
    fields = schema.get("fields") or []
    allowed = {f.get("key"): f for f in fields if f.get("key")}
    data: dict[str, Any] = {}

    for key, field in allowed.items():
        value = raw.get(key)
        if value is None:
            if field.get("required"):
                raise SubmissionValidationError(f"missing required field: {key}")
            continue
        if isinstance(value, str):
            value = value.strip()
        if field.get("required") and not value:
            raise SubmissionValidationError(f"missing required field: {key}")
        if isinstance(value, str):
            max_len = min(int(field.get("max") or settings.INBOX_MAX_FIELD_LENGTH), settings.INBOX_MAX_FIELD_LENGTH)
            if len(value) > max_len:
                raise SubmissionValidationError(f"field too long: {key}")
        data[key] = value

    return data, is_spam
