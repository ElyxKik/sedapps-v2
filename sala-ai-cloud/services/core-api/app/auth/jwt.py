from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.config import settings

TokenType = Literal["access", "refresh"]


def _exp(token_type: TokenType) -> datetime:
    if token_type == "access":
        return datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expires_min)
    return datetime.now(timezone.utc) + timedelta(days=30)


def create_token(sub: str, token_type: TokenType, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": _exp(token_type),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
