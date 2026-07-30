"""Dashboard routes."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: DbSession, user: CurrentUser) -> dict:
    return dashboard_service.dashboard_summary(db, user)
