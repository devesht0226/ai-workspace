"""Chat session and messaging services."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models import ChatSession, Message, MessageRole, UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider


def _default_chat_model() -> tuple[str, str]:
    """Return (provider, model_name) for new chat sessions."""
    settings = get_settings()
    provider = (settings.llm_provider or "ollama").lower()
    if provider in {"openai", "gpt"} and settings.openai_api_key:
        return "openai", settings.openai_chat_model
    if provider == "mistral" and settings.mistral_api_key:
        return "mistral", settings.mistral_chat_model
    if provider in {"huggingface", "hf"} and settings.huggingface_api_key:
        return "huggingface", settings.huggingface_model
    if settings.openai_api_key and provider != "ollama":
        return "openai", settings.openai_chat_model
    return settings.llm_provider, settings.ollama_chat_model


def _chat_model_for_session(session: ChatSession) -> str | None:
    """Avoid sending local Ollama model names to cloud providers."""
    settings = get_settings()
    provider = (settings.llm_provider or session.provider or "").lower()
    name = (session.model_name or "").strip()

    # Cloud OpenAI mode: always use the configured OpenAI model (ignore tinyllama sessions)
    if settings.openai_api_key and provider in {"openai", "gpt"}:
        return settings.openai_chat_model
    if settings.mistral_api_key and provider == "mistral":
        return settings.mistral_chat_model
    if settings.openai_api_key and name in {
        "",
        settings.ollama_chat_model,
        "tinyllama",
        "llama3.2",
    }:
        # Old sessions saved as ollama/tinyllama — still use OpenAI when key exists
        return settings.openai_chat_model
    if provider in {"openai", "gpt"}:
        return name or settings.openai_chat_model
    if provider == "mistral":
        return name or settings.mistral_chat_model
    return name or None


def _llm_for_chat(session: ChatSession):
    """Pick the right backend for this deployment."""
    settings = get_settings()
    provider = (settings.llm_provider or "").lower()
    if settings.openai_api_key and provider in {"openai", "gpt"}:
        return get_llm_provider("gpt")
    if settings.mistral_api_key and provider == "mistral":
        return get_llm_provider("mistral")
    if settings.openai_api_key:
        return get_llm_provider("gpt")
    return get_llm_provider(session.provider or provider or "auto")


def list_sessions(db: Session, user: User) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


def create_session(db: Session, user: User, *, title: str | None = None) -> ChatSession:
    provider, model_name = _default_chat_model()
    session = ChatSession(
        user_id=user.id,
        title=title or "New chat",
        model_name=model_name,
        provider=provider,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, user: User, session_id: UUID) -> ChatSession:
    session = db.scalar(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    if not session:
        raise NotFoundError("Chat session not found")
    return session


def delete_session(db: Session, user: User, session_id: UUID) -> None:
    session = get_session(db, user, session_id)
    db.delete(session)
    db.commit()


def rename_session(db: Session, user: User, session_id: UUID, *, title: str) -> ChatSession:
    session = get_session(db, user, session_id)
    session.title = (title or "Untitled").strip()[:200]
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _history_as_messages(
    session: ChatSession, limit: int = 20, *, memory_context: str | None = None
) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    if memory_context:
        messages.append(
            ChatMessage(
                role="system",
                content=f"Relevant user memory:\n{memory_context}",
            )
        )
    recent = session.messages[-limit:]
    messages.extend(ChatMessage(role=m.role.value, content=m.content) for m in recent)
    return messages


def _memory_snippet(db: Session, user: User, content: str) -> str | None:
    try:
        from app.services import memory as memory_service

        return memory_service.memory_context(db, user, content) or None
    except Exception:
        return None


def send_message_sync(
    db: Session, user: User, session_id: UUID, content: str, *, attachment_text: str | None = None
) -> Message:
    session = get_session(db, user, session_id)
    full_content = content
    if attachment_text:
        full_content = f"{content}\n\n[Attached file excerpt]\n{attachment_text[:6000]}"
    user_msg = Message(session_id=session.id, role=MessageRole.user, content=full_content)
    db.add(user_msg)
    db.commit()
    db.refresh(session)

    llm = _llm_for_chat(session)
    mem = _memory_snippet(db, user, content)
    history = _history_as_messages(session, memory_context=mem)
    reply = llm.chat(history, model=_chat_model_for_session(session))

    assistant = Message(
        session_id=session.id,
        role=MessageRole.assistant,
        content=reply,
        metadata_json={"model": session.model_name, "provider": session.provider},
    )
    db.add(assistant)
    db.add(
        UsageEvent(
            user_id=user.id,
            event_type="chat",
            model_name=session.model_name,
            metadata_json={"session_id": str(session.id)},
        )
    )
    if session.title == "New chat":
        session.title = content[:60]
    db.commit()
    db.refresh(assistant)
    return assistant


def stream_message(db: Session, user: User, session_id: UUID, content: str) -> Iterator[str]:
    """Persist user message, stream tokens, then persist assistant reply.

    Yields SSE data payloads (JSON strings).
    """
    session = get_session(db, user, session_id)
    user_msg = Message(session_id=session.id, role=MessageRole.user, content=content)
    db.add(user_msg)
    if session.title == "New chat":
        session.title = content[:60]
    db.commit()
    db.refresh(session)

    llm = _llm_for_chat(session)
    mem = _memory_snippet(db, user, content)
    history = _history_as_messages(session, memory_context=mem)
    chunks: list[str] = []
    try:
        for token in llm.stream_chat(history, model=_chat_model_for_session(session)):
            chunks.append(token)
            yield json.dumps({"event": "token", "data": token})
        full = "".join(chunks).strip()
        assistant = Message(
            session_id=session.id,
            role=MessageRole.assistant,
            content=full,
            metadata_json={"model": session.model_name, "provider": session.provider},
        )
        db.add(assistant)
        db.add(
            UsageEvent(
                user_id=user.id,
                event_type="chat_stream",
                model_name=session.model_name,
                metadata_json={"session_id": str(session.id)},
            )
        )
        db.commit()
        db.refresh(assistant)
        yield json.dumps(
            {
                "event": "done",
                "data": {"message_id": str(assistant.id), "content": full},
            }
        )
    except Exception as exc:  # noqa: BLE001
        yield json.dumps({"event": "error", "data": str(exc)})


async def astream_message(
    db: Session, user: User, session_id: UUID, content: str
) -> AsyncIterator[str]:
    session = get_session(db, user, session_id)
    user_msg = Message(session_id=session.id, role=MessageRole.user, content=content)
    db.add(user_msg)
    if session.title == "New chat":
        session.title = content[:60]
    db.commit()
    db.refresh(session)

    llm = _llm_for_chat(session)
    mem = _memory_snippet(db, user, content)
    history = _history_as_messages(session, memory_context=mem)
    chunks: list[str] = []
    try:
        async for token in llm.astream_chat(history, model=_chat_model_for_session(session)):
            chunks.append(token)
            yield json.dumps({"event": "token", "data": token})
        full = "".join(chunks).strip()
        assistant = Message(
            session_id=session.id,
            role=MessageRole.assistant,
            content=full,
            metadata_json={"model": session.model_name, "provider": session.provider},
        )
        db.add(assistant)
        db.add(
            UsageEvent(
                user_id=user.id,
                event_type="chat_stream",
                model_name=session.model_name,
                metadata_json={"session_id": str(session.id)},
            )
        )
        db.commit()
        db.refresh(assistant)
        yield json.dumps(
            {
                "event": "done",
                "data": {"message_id": str(assistant.id), "content": full},
            }
        )
    except Exception as exc:  # noqa: BLE001
        yield json.dumps({"event": "error", "data": str(exc)})


def export_session_markdown(db: Session, user: User, session_id: UUID) -> str:
    session = get_session(db, user, session_id)
    lines = [f"# {session.title}", ""]
    for message in session.messages:
        lines.append(f"**{message.role.value}:** {message.content}")
        lines.append("")
    return "\n".join(lines)
