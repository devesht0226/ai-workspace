"""Auth and user profile routes."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
    UserUpdateRequest,
    VerifyEmailRequest,
)
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserPublic, status_code=201)
def register(payload: RegisterRequest, db: DbSession) -> UserPublic:
    user = auth_service.register_user(
        db, email=payload.email, password=payload.password, full_name=payload.full_name
    )
    return auth_service.to_public(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    return auth_service.login_user(db, email=payload.email, password=payload.password)


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    return auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)


@router.post("/auth/logout", status_code=204)
def logout(payload: LogoutRequest, db: DbSession, _: CurrentUser) -> None:
    auth_service.logout_user(db, refresh_token=payload.refresh_token)


@router.post("/auth/logout-all")
def logout_all(db: DbSession, user: CurrentUser) -> dict:
    n = auth_service.logout_all_devices(db, user)
    return {"revoked": n}


@router.post("/auth/verify-email", response_model=UserPublic)
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> UserPublic:
    user = auth_service.verify_email(db, token=payload.token)
    return auth_service.to_public(user)


@router.post("/auth/password-reset/request")
def password_reset_request(payload: PasswordResetRequest, db: DbSession) -> dict:
    return auth_service.request_password_reset(db, email=payload.email)


@router.post("/auth/password-reset/confirm", response_model=UserPublic)
def password_reset_confirm(payload: PasswordResetConfirm, db: DbSession) -> UserPublic:
    user = auth_service.reset_password(db, token=payload.token, new_password=payload.new_password)
    return auth_service.to_public(user)


@router.get("/users/me", response_model=UserPublic)
def me(user: CurrentUser) -> UserPublic:
    return auth_service.to_public(user)


@router.patch("/users/me", response_model=UserPublic)
def update_me(payload: UserUpdateRequest, db: DbSession, user: CurrentUser) -> UserPublic:
    updated = auth_service.update_profile(db, user, full_name=payload.full_name)
    return auth_service.to_public(updated)


@router.post("/users/me/change-password")
def change_password(payload: ChangePasswordRequest, db: DbSession, user: CurrentUser) -> dict:
    auth_service.change_password(
        db,
        user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {"status": "ok"}


@router.get("/users/me/sessions")
def sessions(db: DbSession, user: CurrentUser) -> dict:
    return {"sessions": auth_service.list_sessions(db, user)}


@router.delete("/users/me/sessions/{session_id}", status_code=204)
def revoke_session(session_id: UUID, db: DbSession, user: CurrentUser) -> None:
    auth_service.revoke_session(db, user, session_id)


@router.post("/users/me/avatar", response_model=UserPublic)
async def upload_avatar(
    db: DbSession, user: CurrentUser, file: UploadFile = File(...)
) -> UserPublic:
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise ValidationAppError("Avatar must be under 2MB")
    settings = get_settings()
    avatar_dir = Path(settings.upload_dir) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "avatar.png").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        ext = ".png"
    name = f"{user.id}_{uuid4().hex[:8]}{ext}"
    path = avatar_dir / name
    path.write_bytes(data)
    updated = auth_service.set_avatar(db, user, relative_url=f"/uploads/avatars/{name}")
    return auth_service.to_public(updated)


@router.get("/users/me/export")
def export_me(db: DbSession, user: CurrentUser) -> dict:
    return auth_service.export_account_data(db, user)


@router.delete("/users/me")
def delete_me(db: DbSession, user: CurrentUser) -> dict:
    auth_service.delete_account(db, user)
    return {"status": "deleted"}
