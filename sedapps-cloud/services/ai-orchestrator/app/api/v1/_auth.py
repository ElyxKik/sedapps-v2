from fastapi import Header, HTTPException, status

from app.config import settings


def require_internal(token: str = Header(default="", alias="X-Internal-Token")) -> None:
    if token != settings.INTERNAL_API_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "internal only")
