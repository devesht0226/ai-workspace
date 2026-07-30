"""Admin routes (RBAC protected)."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_admin
from app.models import User
from app.schemas import UserPublic
from app.services import admin as admin_service
from app.services import auth as auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserPublic])
def list_users(
    db: DbSession,
    _: User = Depends(require_admin),
) -> list[UserPublic]:
    return [auth_service.to_public(u) for u in admin_service.list_users(db)]


@router.post("/users/{user_id}/deactivate", response_model=UserPublic)
def deactivate(
    user_id: UUID,
    db: DbSession,
    _: User = Depends(require_admin),
) -> UserPublic:
    user = admin_service.set_user_active(db, user_id, is_active=False)
    return auth_service.to_public(user)


@router.post("/users/{user_id}/activate", response_model=UserPublic)
def activate(
    user_id: UUID,
    db: DbSession,
    _: User = Depends(require_admin),
) -> UserPublic:
    user = admin_service.set_user_active(db, user_id, is_active=True)
    return auth_service.to_public(user)


@router.post("/users/{user_id}/promote", response_model=UserPublic)
def promote(
    user_id: UUID,
    db: DbSession,
    _: User = Depends(require_admin),
) -> UserPublic:
    user = admin_service.promote_admin(db, user_id)
    return auth_service.to_public(user)


@router.get("/stats")
def stats(db: DbSession, _: User = Depends(require_admin)) -> dict:
    return admin_service.platform_stats(db)
