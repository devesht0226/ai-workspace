"""Prompt registry / versioning."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models import PromptTemplate, User

DEFAULT_PROMPTS = {
    "research_assistant": (
        "You are an expert research assistant. Synthesize evidence from documents, "
        "knowledge graph context, and memory. Cite uncertainty clearly."
    ),
    "rag_grounded": (
        "You are a careful assistant for AI Workspace. Answer ONLY using the sources below. "
        "If the sources are insufficient, say you do not know."
    ),
    "sql_expert": (
        "You are a SQL expert. Given the schema, write ONE SQLite SELECT query only. No DML/DDL."
    ),
}


def seed_defaults(db: Session, user: User | None = None) -> None:
    for name, content in DEFAULT_PROMPTS.items():
        exists = db.scalar(select(PromptTemplate).where(PromptTemplate.name == name).limit(1))
        if exists:
            continue
        db.add(
            PromptTemplate(
                name=name,
                version=1,
                content=content,
                model_family="llama",
                created_by=user.email if user else "system",
                is_active=True,
            )
        )
    db.commit()


def list_prompts(db: Session, *, name: str | None = None) -> list[PromptTemplate]:
    stmt = select(PromptTemplate).order_by(PromptTemplate.name, PromptTemplate.version.desc())
    if name:
        stmt = stmt.where(PromptTemplate.name == name)
    return list(db.scalars(stmt).all())


def get_active_prompt(db: Session, name: str) -> PromptTemplate:
    seed_defaults(db)
    row = db.scalar(
        select(PromptTemplate)
        .where(PromptTemplate.name == name, PromptTemplate.is_active.is_(True))
        .order_by(PromptTemplate.version.desc())
    )
    if not row:
        raise NotFoundError(f"Prompt '{name}' not found")
    return row


def create_prompt_version(
    db: Session,
    user: User,
    *,
    name: str,
    content: str,
    model_family: str | None = None,
    performance_score: float | None = None,
) -> PromptTemplate:
    if not content.strip():
        raise ValidationAppError("Prompt content is required")
    latest = db.scalar(select(func.max(PromptTemplate.version)).where(PromptTemplate.name == name))
    version = int(latest or 0) + 1
    # deactivate previous
    for old in db.scalars(select(PromptTemplate).where(PromptTemplate.name == name)).all():
        old.is_active = False
        db.add(old)
    row = PromptTemplate(
        name=name,
        version=version,
        content=content.strip(),
        model_family=model_family,
        created_by=user.email,
        performance_score=performance_score,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
