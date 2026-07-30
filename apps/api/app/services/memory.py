"""Long-term / short-term memory for users and agents."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MemoryEntry, User


def remember(
    db: Session,
    user: User,
    *,
    content: str,
    memory_type: str = "long_term",
    source: str | None = None,
    importance: int = 1,
    metadata: dict | None = None,
) -> MemoryEntry:
    entry = MemoryEntry(
        user_id=user.id,
        content=content.strip(),
        memory_type=memory_type,
        source=source,
        importance=importance,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_memories(
    db: Session, user: User, *, memory_type: str | None = None, limit: int = 50
) -> list[MemoryEntry]:
    stmt = select(MemoryEntry).where(MemoryEntry.user_id == user.id)
    if memory_type:
        stmt = stmt.where(MemoryEntry.memory_type == memory_type)
    stmt = stmt.order_by(MemoryEntry.importance.desc(), MemoryEntry.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def recall(db: Session, user: User, query: str, *, limit: int = 5) -> list[MemoryEntry]:
    q = query.lower()
    memories = list_memories(db, user, limit=100)
    scored = []
    for m in memories:
        score = sum(1 for token in q.split() if token and token in m.content.lower())
        score += m.importance
        if score > 0:
            scored.append((score, m))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [m for _, m in scored[:limit]]


def memory_context(db: Session, user: User, query: str) -> str:
    hits = recall(db, user, query)
    if not hits:
        return ""
    lines = [f"- ({m.memory_type}) {m.content}" for m in hits]
    return "Known memory:\n" + "\n".join(lines)
