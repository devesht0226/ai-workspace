"""Authentication and user profile services."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError, ValidationAppError
from app.core.mailer import send_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, User, UserRole
from app.schemas import TokenResponse, UserPublic


def _token_pair() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def register_user(db: Session, *, email: str, password: str, full_name: str | None) -> User:
    existing = db.scalar(select(User).where(User.email == email.lower()))
    if existing:
        raise ConflictError("Email already registered")
    if len(password) < 8:
        raise ValidationAppError("Password must be at least 8 characters")

    settings = get_settings()
    raw_verify, verify_hash = _token_pair()
    # In tests, auto-verify to keep existing flows simple unless explicitly required
    auto_verified = settings.environment == "test" and not settings.require_email_verification

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        role=UserRole.user,
        email_verified=auto_verified,
        email_verify_token_hash=None if auto_verified else verify_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        from app.services import orgs as org_service

        org_service.ensure_personal_org(db, user)
    except Exception:
        pass

    if not auto_verified:
        link = f"{settings.app_base_url}/verify-email?token={raw_verify}"
        send_email(
            to=user.email,
            subject="Verify your AI Workspace email",
            body=(
                f"Welcome to AI Workspace.\n\n"
                f"Verify your email:\n{link}\n\n"
                f"Or POST /api/v1/auth/verify-email with token={raw_verify}\n"
            ),
        )
    return user


def verify_email(db: Session, *, token: str) -> User:
    token_hash = hash_token(token)
    user = db.scalar(select(User).where(User.email_verify_token_hash == token_hash))
    if not user:
        raise ValidationAppError("Invalid or expired verification token")
    user.email_verified = True
    user.email_verify_token_hash = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def request_password_reset(db: Session, *, email: str) -> dict:
    user = db.scalar(select(User).where(User.email == email.lower()))
    # Always return ok to avoid email enumeration
    if not user:
        return {"status": "ok"}
    raw, token_hash = _token_pair()
    user.password_reset_token_hash = token_hash
    user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(user)
    db.commit()
    settings = get_settings()
    link = f"{settings.app_base_url}/reset-password?token={raw}"
    send_email(
        to=user.email,
        subject="Reset your AI Workspace password",
        body=f"Reset your password:\n{link}\n\nToken: {raw}\nThis link expires in 1 hour.\n",
    )
    return {"status": "ok"}


def reset_password(db: Session, *, token: str, new_password: str) -> User:
    if len(new_password) < 8:
        raise ValidationAppError("Password must be at least 8 characters")
    token_hash = hash_token(token)
    user = db.scalar(select(User).where(User.password_reset_token_hash == token_hash))
    if not user or not user.password_reset_expires_at:
        raise ValidationAppError("Invalid or expired reset token")
    expires = user.password_reset_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise ValidationAppError("Invalid or expired reset token")
    user.password_hash = hash_password(new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    settings = get_settings()
    access = create_access_token(subject=str(user.id), role=user.role.value)
    refresh, jti, expires = create_refresh_token(subject=str(user.id))
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            jti=jti,
            expires_at=expires,
        )
    )
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_ttl_seconds,
    )


def login_user(db: Session, *, email: str, password: str) -> TokenResponse:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("User is inactive")
    if settings.require_email_verification and not user.email_verified:
        raise ForbiddenError("Email not verified. Check your inbox or mail dump.")
    return _issue_tokens(db, user)


def refresh_access_token(db: Session, *, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise UnauthorizedError("Invalid refresh token") from exc
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise UnauthorizedError("Invalid refresh token")

    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    expires_at = stored.expires_at if stored else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        not stored
        or stored.revoked
        or stored.token_hash != hash_token(refresh_token)
        or expires_at is None
        or expires_at < datetime.now(timezone.utc)
    ):
        raise UnauthorizedError("Refresh token revoked or expired")

    user = db.get(User, UUID(sub))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    stored.revoked = True
    db.commit()
    return _issue_tokens(db, user)


def logout_user(db: Session, *, refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        return
    jti = payload.get("jti")
    if not jti:
        return
    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if stored and not stored.revoked:
        stored.revoked = True
        db.commit()


def to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        email_verified=bool(user.email_verified),
        avatar_url=getattr(user, "avatar_url", None),
        created_at=user.created_at,
    )


def update_profile(db: Session, user: User, *, full_name: str | None) -> User:
    if full_name is not None:
        user.full_name = full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, *, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    if len(new_password) < 8:
        raise ValidationAppError("Password must be at least 8 characters")
    user.password_hash = hash_password(new_password)
    db.add(user)
    # revoke all sessions
    for tok in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)).all():
        tok.revoked = True
        db.add(tok)
    db.commit()


def list_sessions(db: Session, user: User) -> list[dict]:
    rows = list(
        db.scalars(
            select(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
            .order_by(RefreshToken.created_at.desc())
        ).all()
    )
    return [
        {
            "id": str(r.id),
            "jti": r.jti,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "user_agent": getattr(r, "user_agent", None),
        }
        for r in rows
    ]


def revoke_session(db: Session, user: User, session_id: UUID) -> None:
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.id == session_id, RefreshToken.user_id == user.id)
    )
    if not row:
        raise ValidationAppError("Session not found")
    row.revoked = True
    db.add(row)
    db.commit()


def logout_all_devices(db: Session, user: User) -> int:
    rows = list(db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)).all())
    for r in rows:
        r.revoked = True
        db.add(r)
    db.commit()
    return len(rows)


def set_avatar(db: Session, user: User, *, relative_url: str) -> User:
    user.avatar_url = relative_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_account(db: Session, user: User) -> None:
    """GDPR-style account wipe — cascade ORM deletes + vector cleanup best-effort."""
    from pathlib import Path

    from app.models import Document
    from app.providers.vector_store import get_memory_store

    docs = list(db.scalars(select(Document).where(Document.user_id == user.id)).all())
    for doc in docs:
        try:
            get_memory_store().delete_by_document(str(doc.id))
        except Exception:
            pass
        path = Path(doc.storage_path)
        if path.exists():
            path.unlink(missing_ok=True)
    db.delete(user)
    db.commit()


def export_account_data(db: Session, user: User) -> dict:
    """GDPR-style portable export of the user's primary workspace data."""
    from app.models import (
        AgentRun,
        ChatSession,
        Document,
        MeetingNote,
        Message,
        Notification,
        ResumeAnalysis,
        UsageEvent,
    )

    chats = list(db.scalars(select(ChatSession).where(ChatSession.user_id == user.id)).all())
    chat_payload = []
    for chat in chats:
        messages = list(
            db.scalars(
                select(Message).where(Message.session_id == chat.id).order_by(Message.created_at)
            ).all()
        )
        chat_payload.append(
            {
                "id": str(chat.id),
                "title": chat.title,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
                "messages": [
                    {
                        "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ],
            }
        )

    docs = list(db.scalars(select(Document).where(Document.user_id == user.id)).all())
    meetings = list(db.scalars(select(MeetingNote).where(MeetingNote.user_id == user.id)).all())
    resumes = list(
        db.scalars(select(ResumeAnalysis).where(ResumeAnalysis.user_id == user.id)).all()
    )
    agents = list(db.scalars(select(AgentRun).where(AgentRun.user_id == user.id)).all())
    notes = list(db.scalars(select(Notification).where(Notification.user_id == user.id)).all())
    usage = list(
        db.scalars(
            select(UsageEvent)
            .where(UsageEvent.user_id == user.id)
            .order_by(UsageEvent.created_at.desc())
            .limit(200)
        ).all()
    )

    return {
        "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "chats": chat_payload,
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "meetings": [
            {
                "id": str(m.id),
                "title": m.title,
                "summary": m.summary,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in meetings
        ],
        "resumes": [
            {
                "id": str(r.id),
                "filename": r.filename,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resumes
        ],
        "agent_runs": [
            {
                "id": str(a.id),
                "task": a.task,
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in agents
        ],
        "notifications": [
            {
                "id": str(n.id),
                "title": n.title,
                "body": n.body,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "usage_events": [
            {
                "event_type": u.event_type,
                "model_name": u.model_name,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in usage
        ],
    }
