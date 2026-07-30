"""Meeting notes routes."""

from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.deps import CurrentUser, DbSession
from app.schemas import MeetingOut
from app.services import meetings as meeting_service

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _out(row) -> MeetingOut:
    return MeetingOut(
        id=row.id,
        title=row.title,
        filename=row.filename,
        status=row.status.value,
        transcript=row.transcript,
        summary=row.summary,
        action_items_json=row.action_items_json,
        decisions_json=row.decisions_json,
        follow_up_email=row.follow_up_email,
        error_message=row.error_message,
        created_at=row.created_at,
    )


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    db: DbSession, user: CurrentUser, q: str | None = None
) -> list[MeetingOut]:
    rows = (
        meeting_service.search_meetings(db, user, q)
        if q is not None
        else meeting_service.list_meetings(db, user)
    )
    return [_out(m) for m in rows]


@router.post("", response_model=MeetingOut, status_code=201)
async def create_meeting(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile | None = File(default=None),
    title: str | None = Form(default=None),
    transcript: str | None = Form(default=None),
) -> MeetingOut:
    data = await file.read() if file is not None else None
    filename = file.filename if file is not None else None
    row = meeting_service.create_meeting_note(
        db,
        user,
        filename=filename,
        data=data,
        title=title,
        transcript_text=transcript,
    )
    return _out(row)


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: UUID, db: DbSession, user: CurrentUser) -> MeetingOut:
    return _out(meeting_service.get_meeting(db, user, meeting_id))


@router.get("/{meeting_id}/export")
def export_meeting(meeting_id: UUID, db: DbSession, user: CurrentUser) -> PlainTextResponse:
    content = meeting_service.export_meeting_markdown(db, user, meeting_id)
    return PlainTextResponse(content, media_type="text/markdown")
