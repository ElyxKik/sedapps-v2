from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="SedApps Deploy Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "deploy-service"}


app.include_router(api_router)
