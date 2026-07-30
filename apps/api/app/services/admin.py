"""Admin service and helpers."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import UsageEvent, User, UserRole


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def set_user_active(db: Session, user_id, *, is_active: bool) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    user.is_active = is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def promote_admin(db: Session, user_id) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    user.role = UserRole.admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def platform_stats(db: Session) -> dict:
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "usage_events": db.scalar(select(func.count()).select_from(UsageEvent)) or 0,
        "verified_users": db.scalar(
            select(func.count()).select_from(User).where(User.email_verified.is_(True))
        )
        or 0,
    }
