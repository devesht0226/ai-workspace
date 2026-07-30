"""Dashboard aggregates for activity, usage, and workspace inventory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AgentRun,
    ChatSession,
    CodeReview,
    Document,
    MeetingNote,
    ResumeAnalysis,
    UsageEvent,
    User,
)
from app.services import notifications as notif_service


def dashboard_summary(db: Session, user: User) -> dict:
    docs = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id))
    chats = db.scalar(
        select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user.id)
    )
    reviews = db.scalar(
        select(func.count()).select_from(CodeReview).where(CodeReview.user_id == user.id)
    )
    resumes = db.scalar(
        select(func.count()).select_from(ResumeAnalysis).where(ResumeAnalysis.user_id == user.id)
    )
    meetings = db.scalar(
        select(func.count()).select_from(MeetingNote).where(MeetingNote.user_id == user.id)
    )
    agents = db.scalar(
        select(func.count()).select_from(AgentRun).where(AgentRun.user_id == user.id)
    )

    usage_rows = list(
        db.scalars(
            select(UsageEvent)
            .where(UsageEvent.user_id == user.id)
            .order_by(UsageEvent.created_at.desc())
            .limit(20)
        ).all()
    )
    usage_by_type: dict[str, int] = {}
    model_usage: dict[str, int] = {}
    token_in = 0
    token_out = 0
    for event in db.scalars(select(UsageEvent).where(UsageEvent.user_id == user.id)).all():
        usage_by_type[event.event_type] = usage_by_type.get(event.event_type, 0) + 1
        if event.model_name:
            model_usage[event.model_name] = model_usage.get(event.model_name, 0) + 1
        token_in += event.input_tokens or 0
        token_out += event.output_tokens or 0

    storage_bytes = 0
    for d in db.scalars(select(Document).where(Document.user_id == user.id)).all():
        try:
            storage_bytes += Path(d.storage_path).stat().st_size
        except Exception:
            pass

    recent_docs = list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
            .limit(5)
        ).all()
    )
    recent_chats = list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.updated_at.desc())
            .limit(5)
        ).all()
    )
    recent_agents = list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.user_id == user.id)
            .order_by(AgentRun.created_at.desc())
            .limit(5)
        ).all()
    )
    recent_meetings = list(
        db.scalars(
            select(MeetingNote)
            .where(MeetingNote.user_id == user.id)
            .order_by(MeetingNote.created_at.desc())
            .limit(5)
        ).all()
    )

    return {
        "counts": {
            "documents": docs or 0,
            "chats": chats or 0,
            "code_reviews": reviews or 0,
            "resumes": resumes or 0,
            "meetings": meetings or 0,
            "agent_runs": agents or 0,
        },
        "usage_by_type": usage_by_type,
        "model_usage": model_usage,
        "token_usage": {"input": token_in, "output": token_out, "total": token_in + token_out},
        "storage_bytes": storage_bytes,
        "unread_notifications": notif_service.unread_count(db, user),
        "recent_activity": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "model_name": e.model_name,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "metadata": e.metadata_json or {},
            }
            for e in usage_rows
        ],
        "recent_documents": [
            {"id": str(d.id), "filename": d.filename, "status": d.status.value} for d in recent_docs
        ],
        "recent_chats": [
            {"id": str(c.id), "title": c.title, "updated_at": c.updated_at.isoformat()}
            for c in recent_chats
        ],
        "recent_agent_runs": [
            {
                "id": str(a.id),
                "task": a.task[:120],
                "status": a.status.value,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_agents
        ],
        "recent_meetings": [
            {"id": str(m.id), "title": m.title, "status": m.status.value} for m in recent_meetings
        ],
        "settings": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "avatar_url": getattr(user, "avatar_url", None),
        },
    }
