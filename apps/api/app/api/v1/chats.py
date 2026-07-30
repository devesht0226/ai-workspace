"""Chat routes."""

from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas import (
    ChatCreateRequest,
    ChatSessionDetail,
    ChatSessionOut,
    MessageOut,
    SendMessageRequest,
)
from app.services import chat as chat_service

router = APIRouter(prefix="/chats", tags=["chats"])


class RenameChatRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@router.get("", response_model=list[ChatSessionOut])
def list_chats(db: DbSession, user: CurrentUser) -> list[ChatSessionOut]:
    return [ChatSessionOut.model_validate(s) for s in chat_service.list_sessions(db, user)]


@router.post("", response_model=ChatSessionOut, status_code=201)
def create_chat(payload: ChatCreateRequest, db: DbSession, user: CurrentUser) -> ChatSessionOut:
    session = chat_service.create_session(db, user, title=payload.title)
    return ChatSessionOut.model_validate(session)


@router.get("/{session_id}", response_model=ChatSessionDetail)
def get_chat(session_id: UUID, db: DbSession, user: CurrentUser) -> ChatSessionDetail:
    session = chat_service.get_session(db, user, session_id)
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        model_name=session.model_name,
        provider=session.provider,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                metadata_json=m.metadata_json,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )


@router.delete("/{session_id}", status_code=204)
def delete_chat(session_id: UUID, db: DbSession, user: CurrentUser) -> None:
    chat_service.delete_session(db, user, session_id)


@router.patch("/{session_id}", response_model=ChatSessionOut)
def rename_chat(
    session_id: UUID, payload: RenameChatRequest, db: DbSession, user: CurrentUser
) -> ChatSessionOut:
    session = chat_service.rename_session(db, user, session_id, title=payload.title)
    return ChatSessionOut.model_validate(session)


@router.post("/{session_id}/messages")
async def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    db: DbSession,
    user: CurrentUser,
):
    if payload.stream:

        async def event_generator():
            async for chunk in chat_service.astream_message(db, user, session_id, payload.content):
                yield f"data: {chunk}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    message = chat_service.send_message_sync(db, user, session_id, payload.content)
    return MessageOut(
        id=message.id,
        role=message.role.value,
        content=message.content,
        metadata_json=message.metadata_json,
        created_at=message.created_at,
    )


@router.post("/{session_id}/messages/upload")
async def send_message_with_file(
    session_id: UUID,
    db: DbSession,
    user: CurrentUser,
    content: str = Form(...),
    file: UploadFile | None = File(None),
):
    attachment_text = None
    if file is not None:
        raw = await file.read()
        try:
            attachment_text = raw.decode("utf-8", errors="ignore")[:8000]
        except Exception:
            attachment_text = None
    message = chat_service.send_message_sync(
        db, user, session_id, content, attachment_text=attachment_text
    )
    return MessageOut(
        id=message.id,
        role=message.role.value,
        content=message.content,
        metadata_json=message.metadata_json,
        created_at=message.created_at,
    )


@router.get("/{session_id}/export")
def export_chat(session_id: UUID, db: DbSession, user: CurrentUser) -> PlainTextResponse:
    content = chat_service.export_session_markdown(db, user, session_id)
    return PlainTextResponse(content, media_type="text/markdown")
