"""Human feedback loop API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import feedback as feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    target_type: str = Field(min_length=1, max_length=50)
    rating: int = Field(description="1 = good, -1 = bad")
    target_id: str | None = Field(default=None, max_length=64)
    comment: str | None = Field(default=None, max_length=2000)
    answer_snapshot: str | None = Field(default=None, max_length=20000)
    metadata: dict | None = None


@router.post("")
def submit_feedback(payload: FeedbackRequest, db: DbSession, user: CurrentUser) -> dict:
    row = feedback_service.submit_feedback(
        db,
        user,
        target_type=payload.target_type,
        rating=payload.rating,
        target_id=payload.target_id,
        comment=payload.comment,
        answer_snapshot=payload.answer_snapshot,
        metadata=payload.metadata,
    )
    return {
        "id": str(row.id),
        "target_type": row.target_type,
        "rating": row.rating,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("")
def list_feedback(db: DbSession, user: CurrentUser, limit: int = 100) -> dict:
    rows = feedback_service.list_feedback(db, user, limit=min(limit, 200))
    return {
        "feedback": [
            {
                "id": str(r.id),
                "target_type": r.target_type,
                "target_id": r.target_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.get("/summary")
def feedback_summary(db: DbSession, user: CurrentUser) -> dict:
    return feedback_service.feedback_summary(db, user)
