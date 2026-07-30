"""Memory API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import memory as memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


class RememberRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    memory_type: str = Field(default="long_term", max_length=50)
    importance: int = Field(default=1, ge=1, le=10)


@router.get("")
def list_memory(db: DbSession, user: CurrentUser) -> list[dict]:
    rows = memory_service.list_memories(db, user)
    return [
        {
            "id": str(r.id),
            "memory_type": r.memory_type,
            "content": r.content,
            "source": r.source,
            "importance": r.importance,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("")
def remember(payload: RememberRequest, db: DbSession, user: CurrentUser) -> dict:
    row = memory_service.remember(
        db,
        user,
        content=payload.content,
        memory_type=payload.memory_type,
        importance=payload.importance,
        source="api",
    )
    return {"id": str(row.id), "content": row.content, "memory_type": row.memory_type}


@router.get("/recall")
def recall(q: str, db: DbSession, user: CurrentUser) -> dict:
    hits = memory_service.recall(db, user, q)
    return {
        "query": q,
        "hits": [{"content": h.content, "type": h.memory_type} for h in hits],
    }
