from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.config import settings

TokenType = Literal["access", "refresh"]


def _exp(token_type: TokenType) -> datetime:
    if token_type == "access":
        return datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS)


def create_token(sub: str, token_type: TokenType, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": _exp(token_type),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
