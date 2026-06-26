from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import AnalyticsEvent
from app.schemas import EventIn
from app.tracker import TRACKER_JS

app = FastAPI(title="SedApps Analytics Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analytics-service"}


@app.get("/tracker.js")
def tracker_js() -> Response:
    return Response(
        TRACKER_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"},
    )


def _uuid_or_none(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


@app.post("/v1/events", status_code=status.HTTP_202_ACCEPTED)
def ingest_event(body: EventIn, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    if settings.ANALYTICS_RESPECT_DNT and request.headers.get("dnt") == "1":
        return {"status": "ignored"}
    event = AnalyticsEvent(
        tracker_id=body.tracker_id,
        tenant_id=_uuid_or_none(body.tenant_id),
        project_id=_uuid_or_none(body.project_id),
        session_id=body.session_id,
        event=body.event,
        path=body.path,
        referrer=body.referrer,
        user_agent=request.headers.get("user-agent", "")[:500],
        ip=request.client.host if request.client else None,
        metadata_json=body.metadata,
    )
    db.add(event)
    db.commit()
    return {"status": "accepted"}
