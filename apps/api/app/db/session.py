"""SQLAlchemy base and session factory."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def configure_engine(database_url: str | None = None) -> Engine:
    """Create (or recreate) the global engine and session factory."""
    global engine, SessionLocal
    settings = get_settings()
    url = database_url or settings.database_url
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
            url = "sqlite://"
    else:
        kwargs["pool_pre_ping"] = True
    engine = create_engine(url, **kwargs)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    return engine


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        configure_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and apply lightweight SQLite column patches."""
    from sqlalchemy import text

    from app import models  # noqa: F401

    if engine is None:
        configure_engine()
    assert engine is not None
    Base.metadata.create_all(bind=engine)

    # Best-effort ALTER for existing SQLite DBs (ignore if column exists).
    patches = [
        ("users", "avatar_url", "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"),
        (
            "refresh_tokens",
            "user_agent",
            "ALTER TABLE refresh_tokens ADD COLUMN user_agent VARCHAR(300)",
        ),
        ("documents", "collection_id", "ALTER TABLE documents ADD COLUMN collection_id CHAR(36)"),
        ("documents", "content_hash", "ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64)"),
        ("documents", "version", "ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1"),
        (
            "documents",
            "parent_document_id",
            "ALTER TABLE documents ADD COLUMN parent_document_id CHAR(36)",
        ),
        (
            "meeting_notes",
            "decisions_json",
            "ALTER TABLE meeting_notes ADD COLUMN decisions_json JSON",
        ),
        (
            "meeting_notes",
            "follow_up_email",
            "ALTER TABLE meeting_notes ADD COLUMN follow_up_email TEXT",
        ),
    ]
    url = str(engine.url)
    if url.startswith("sqlite"):
        with engine.begin() as conn:
            for _table, _col, stmt in patches:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass


# Default engine for normal app import (tests may reconfigure).
configure_engine()
