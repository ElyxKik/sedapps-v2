from fastapi import APIRouter

from app.api.v1 import agents, workflows

api_router = APIRouter(prefix="/v1")
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
