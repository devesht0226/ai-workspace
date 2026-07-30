"""Meeting Notes: transcript, summary, action items."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.validation import ALLOWED_MEETING, validate_upload
from app.models import JobStatus, MeetingNote, UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider
from app.providers.stt import get_stt_provider


def _upload_dir() -> Path:
    path = Path(get_settings().upload_dir) / "meetings"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _transcribe(filename: str, data: bytes, provided_transcript: str | None) -> str:
    if provided_transcript and provided_transcript.strip():
        return provided_transcript.strip()
    lower = filename.lower()
    if lower.endswith((".txt", ".md", ".vtt", ".srt")):
        return data.decode("utf-8", errors="replace")
    stt = get_stt_provider()
    if stt is not None:
        return stt.transcribe(filename=filename, data=data)
    raise ValidationAppError(
        "Audio STT is not configured. Set OLLAMA_WHISPER_MODEL, use llm_provider=fake for demos, "
        "or upload a .txt/.vtt transcript."
    )


def _action_items_from_text(text: str) -> list[dict]:
    items: list[dict] = []
    for line in text.splitlines():
        if re.search(r"action item|todo|follow up|we need to|will prepare", line, re.I):
            items.append({"text": line.strip(), "done": False})
    if not items:
        items.append({"text": "Review meeting summary and assign owners", "done": False})
    return items[:12]


def _decisions_from_text(text: str) -> list[str]:
    decisions = [
        line.strip()
        for line in text.splitlines()
        if re.search(r"\b(decided|decision|agreed|approved|will proceed)\b", line, re.I)
    ]
    return decisions[:12]


def _follow_up_email(summary: str, actions: list[dict], decisions: list[str]) -> str:
    action_text = "\n".join(f"- {item.get('text', '')}" for item in actions)
    decision_text = "\n".join(f"- {decision}" for decision in decisions) or "- No decisions captured."
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return (
            "Subject: Meeting follow-up\n\n"
            f"Thanks for the discussion. Summary: {summary}\n\nDecisions:\n{decision_text}"
            f"\n\nNext steps:\n{action_text}"
        )
    try:
        return get_llm_provider().chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "Draft a concise professional follow-up email from this meeting summary, "
                        "decisions, and action items.\n\n"
                        f"SUMMARY: {summary}\nDECISIONS:\n{decision_text}\nACTIONS:\n{action_text}"
                    ),
                )
            ]
        )
    except Exception:
        return f"Subject: Meeting follow-up\n\n{summary}\n\nNext steps:\n{action_text}"


def create_meeting_note(
    db: Session,
    user: User,
    *,
    filename: str | None,
    data: bytes | None,
    title: str | None = None,
    transcript_text: str | None = None,
) -> MeetingNote:
    if not data and not transcript_text:
        raise ValidationAppError("Provide an audio/transcript file or transcript text")

    note_id = uuid4()
    storage_path = None
    fname = filename or "transcript.txt"
    if data:
        validate_upload(
            filename=fname,
            data=data,
            allowed_extensions=ALLOWED_MEETING,
        )
        storage_path = str(_upload_dir() / f"{note_id}_{fname}")
        Path(storage_path).write_bytes(data)

    note = MeetingNote(
        id=note_id,
        user_id=user.id,
        title=title or f"Meeting: {fname}",
        filename=fname,
        storage_path=storage_path,
        status=JobStatus.processing,
    )
    db.add(note)
    db.commit()

    try:
        transcript = _transcribe(fname, data or b"", transcript_text)
        llm = get_llm_provider()
        if get_settings().environment == "test" or get_settings().llm_provider == "fake":
            summary = (
                "Weekly planning covered SQL assistant delivery and dashboard design follow-up."
            )
        else:
            summary = llm.chat(
                [
                    ChatMessage(
                        role="user",
                        content=f"Summarize this meeting transcript in 5 sentences:\n{transcript[:6000]}",
                    )
                ]
            )
        actions = _action_items_from_text(transcript)
        decisions = _decisions_from_text(transcript)
        note.transcript = transcript
        note.summary = summary
        note.action_items_json = actions
        note.decisions_json = decisions
        note.follow_up_email = _follow_up_email(summary, actions, decisions)
        note.status = JobStatus.ready
        note.error_message = None
    except Exception as exc:  # noqa: BLE001
        note.status = JobStatus.failed
        note.error_message = str(exc)
        db.add(note)
        db.commit()
        db.refresh(note)
        raise

    db.add(note)
    db.add(
        UsageEvent(
            user_id=user.id,
            event_type="meeting_notes",
            model_name=get_settings().ollama_chat_model,
            metadata_json={"meeting_id": str(note.id)},
        )
    )
    db.commit()
    db.refresh(note)
    try:
        from app.services import notifications

        notifications.notify(
            db,
            user,
            title="Meeting notes ready",
            body=f"{note.title} is ready to review.",
            category="meeting",
            link=f"/meetings/{note.id}",
        )
    except Exception:
        pass
    return note


def list_meetings(db: Session, user: User) -> list[MeetingNote]:
    return list(
        db.scalars(
            select(MeetingNote)
            .where(MeetingNote.user_id == user.id)
            .order_by(MeetingNote.created_at.desc())
        ).all()
    )


def search_meetings(db: Session, user: User, q: str) -> list[MeetingNote]:
    term = q.strip()
    if not term:
        return list_meetings(db, user)
    pattern = f"%{term}%"
    return list(
        db.scalars(
            select(MeetingNote)
            .where(
                MeetingNote.user_id == user.id,
                (
                    MeetingNote.title.ilike(pattern)
                    | MeetingNote.transcript.ilike(pattern)
                    | MeetingNote.summary.ilike(pattern)
                ),
            )
            .order_by(MeetingNote.created_at.desc())
        ).all()
    )


def get_meeting(db: Session, user: User, meeting_id) -> MeetingNote:
    note = db.scalar(
        select(MeetingNote).where(MeetingNote.id == meeting_id, MeetingNote.user_id == user.id)
    )
    if not note:
        raise NotFoundError("Meeting note not found")
    return note


def export_meeting_markdown(db: Session, user: User, meeting_id) -> str:
    note = get_meeting(db, user, meeting_id)
    lines = [
        f"# {note.title}",
        "",
        "## Summary",
        note.summary or "",
        "",
        "## Action items",
    ]
    for item in note.action_items_json or []:
        lines.append(f"- [ ] {item.get('text', '')}")
    lines.extend(["", "## Decisions"])
    for decision in note.decisions_json or []:
        lines.append(f"- {decision}")
    lines.extend(["", "## Follow-up email", note.follow_up_email or ""])
    lines.extend(["", "## Transcript", note.transcript or ""])
    return "\n".join(lines)
