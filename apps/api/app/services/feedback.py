"""Human feedback loop."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationAppError
from app.models import FeedbackEvent, User


def submit_feedback(
    db: Session,
    user: User,
    *,
    target_type: str,
    rating: int,
    target_id: str | None = None,
    comment: str | None = None,
    answer_snapshot: str | None = None,
    metadata: dict | None = None,
) -> FeedbackEvent:
    if rating not in {-1, 1}:
        raise ValidationAppError("rating must be 1 (good) or -1 (bad)")
    row = FeedbackEvent(
        user_id=user.id,
        target_type=target_type,
        target_id=target_id,
        rating=rating,
        comment=comment,
        answer_snapshot=answer_snapshot,
        metadata_json=metadata or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_feedback(db: Session, user: User, *, limit: int = 100) -> list[FeedbackEvent]:
    return list(
        db.scalars(
            select(FeedbackEvent)
            .where(FeedbackEvent.user_id == user.id)
            .order_by(FeedbackEvent.created_at.desc())
            .limit(limit)
        ).all()
    )


def feedback_summary(db: Session, user: User) -> dict:
    rows = list(db.scalars(select(FeedbackEvent).where(FeedbackEvent.user_id == user.id)).all())
    good = sum(1 for r in rows if r.rating > 0)
    bad = sum(1 for r in rows if r.rating < 0)
    by_type: dict[str, dict[str, int]] = {}
    for r in rows:
        bucket = by_type.setdefault(r.target_type, {"good": 0, "bad": 0})
        if r.rating > 0:
            bucket["good"] += 1
        else:
            bucket["bad"] += 1
    return {
        "total": len(rows),
        "good": good,
        "bad": bad,
        "approval_rate": round(good / len(rows), 4) if rows else None,
        "by_type": by_type,
    }
