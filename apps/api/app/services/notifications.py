"""In-app notifications."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Notification, User


def notify(
    db: Session,
    user: User,
    *,
    title: str,
    body: str,
    category: str = "system",
    link: str | None = None,
) -> Notification:
    row = Notification(
        user_id=user.id,
        title=title,
        body=body,
        category=category,
        link=link,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_notifications(db: Session, user: User, *, limit: int = 50) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).all()
    )


def unread_count(db: Session, user: User) -> int:
    return len(
        [
            n
            for n in db.scalars(
                select(Notification).where(
                    Notification.user_id == user.id, Notification.is_read.is_(False)
                )
            ).all()
        ]
    )


def mark_read(db: Session, user: User, notification_id: UUID) -> Notification:
    row = db.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    )
    if not row:
        raise NotFoundError("Notification not found")
    row.is_read = True
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mark_all_read(db: Session, user: User) -> int:
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user.id, Notification.is_read.is_(False)
            )
        ).all()
    )
    for r in rows:
        r.is_read = True
        db.add(r)
    db.commit()
    return len(rows)


def to_dict(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "title": n.title,
        "body": n.body,
        "category": n.category,
        "link": n.link,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
