from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_org_db
from app.models.ai_job import AgentRun, AiJob

router = APIRouter()


@router.get("/{job_id}")
def get_job(job_id: uuid.UUID, db: Session = Depends(get_current_org_db)) -> dict:
    job = db.get(AiJob, job_id)
    if not job or job.tenant_id != db.info["tenant_id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    runs = (
        db.query(AgentRun)
        .filter(AgentRun.job_id == job.id)
        .order_by(AgentRun.created_at.asc())
        .all()
    )
    return {
        "id": str(job.id),
        "status": job.status.value,
        "workflow": job.workflow,
        "error": job.error,
        "tokens_in": job.tokens_in,
        "tokens_out": job.tokens_out,
        "cost_cents": job.cost_cents,
        "input": job.input,
        "output": job.output,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "agents": [
            {
                "id": str(r.id),
                "name": r.agent_name,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "model": r.model,
                "prompt_version": r.prompt_version,
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "input": r.input,
                "output": r.output,
                "warnings": r.warnings,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }
