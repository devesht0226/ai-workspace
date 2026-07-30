"""Notification routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.services import notifications as notif_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(db: DbSession, user: CurrentUser) -> dict:
    rows = notif_service.list_notifications(db, user)
    return {
        "notifications": [notif_service.to_dict(n) for n in rows],
        "unread": notif_service.unread_count(db, user),
    }


@router.post("/{notification_id}/read")
def mark_read(notification_id: UUID, db: DbSession, user: CurrentUser) -> dict:
    return notif_service.to_dict(notif_service.mark_read(db, user, notification_id))


@router.post("/read-all")
def read_all(db: DbSession, user: CurrentUser) -> dict:
    return {"marked": notif_service.mark_all_read(db, user)}
