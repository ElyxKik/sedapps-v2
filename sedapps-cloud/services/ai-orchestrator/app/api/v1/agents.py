"""Endpoints de debug pour exécuter un agent en isolation (utile en dev)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents import AGENT_REGISTRY, AgentInput
from app.api.v1._auth import require_internal

router = APIRouter()


class AgentRunIn(BaseModel):
    project_id: str = "00000000-0000-0000-0000-000000000000"
    job_id: str = "00000000-0000-0000-0000-000000000000"
    tenant_id: str = "00000000-0000-0000-0000-000000000000"
    locale: str = "fr"
    context: dict[str, Any] = {}
    params: dict[str, Any] = {}


@router.get("")
def list_agents() -> dict[str, list[str]]:
    return {"agents": sorted(AGENT_REGISTRY.keys())}


@router.post("/{name}/run", dependencies=[Depends(require_internal)])
async def run_agent(name: str, body: AgentRunIn) -> dict[str, Any]:
    cls = AGENT_REGISTRY.get(name)
    if not cls:
        raise HTTPException(404, f"unknown agent '{name}'")
    out = await cls().run(AgentInput(**body.model_dump()))
    return out.model_dump()
