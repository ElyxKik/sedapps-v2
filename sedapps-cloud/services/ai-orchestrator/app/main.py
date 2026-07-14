from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

app = FastAPI(
    title="SedApps AI Orchestrator",
    version="0.1.0",
    description="Multi-agents IA spécialisés (DeepSeek V4) + workflows Celery",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-orchestrator",
        "model": settings.LLM_MODEL,
    }


app.include_router(api_router)
