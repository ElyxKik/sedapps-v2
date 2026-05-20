from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import deployments

api_router = APIRouter(prefix="/v1")
api_router.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
