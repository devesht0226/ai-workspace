"""Agent observability / execution traces."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.services import tracing

router = APIRouter(prefix="/traces", tags=["observability"])


@router.get("")
def list_traces(db: DbSession, user: CurrentUser, limit: int = 50) -> dict:
    rows = tracing.list_traces(db, user, limit=min(limit, 100))
    return {
        "traces": [
            {
                "id": str(t.id),
                "request_text": t.request_text,
                "status": t.status,
                "model_family": t.model_family,
                "total_latency_ms": t.total_latency_ms,
                "total_tokens": t.total_tokens,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in rows
        ]
    }


@router.get("/{trace_id}")
def get_trace(trace_id: UUID, db: DbSession, user: CurrentUser) -> dict:
    return tracing.trace_to_dict(tracing.get_trace(db, user, trace_id))
