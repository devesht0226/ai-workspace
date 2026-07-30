"""Organizations and teams."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.models import Organization, OrganizationMember, Team, TeamMember, User


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:100] or "org"


def create_organization(db: Session, user: User, *, name: str) -> Organization:
    if not name.strip():
        raise ValidationAppError("Organization name is required")
    base = _slugify(name)
    slug = base
    i = 1
    while db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base}-{i}"
        i += 1
    org = Organization(name=name.strip(), slug=slug, owner_id=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="owner"))
    db.commit()
    db.refresh(org)
    return org


def ensure_personal_org(db: Session, user: User) -> Organization:
    existing = db.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id).limit(1)
    )
    if existing:
        org = db.get(Organization, existing.organization_id)
        if org:
            return org
    return create_organization(db, user, name=f"{user.full_name or user.email.split('@')[0]}'s Org")


def list_organizations(db: Session, user: User) -> list[dict]:
    memberships = list(
        db.scalars(select(OrganizationMember).where(OrganizationMember.user_id == user.id)).all()
    )
    out = []
    for m in memberships:
        org = db.get(Organization, m.organization_id)
        if not org:
            continue
        out.append(
            {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "role": m.role,
                "owner_id": str(org.owner_id),
            }
        )
    return out


def _require_member(db: Session, user: User, org_id: UUID) -> OrganizationMember:
    m = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if not m:
        raise ForbiddenError("Not a member of this organization")
    return m


def add_member(db: Session, user: User, org_id: UUID, *, email: str, role: str = "member") -> dict:
    _require_member(db, user, org_id)
    target = db.scalar(select(User).where(User.email == email.lower()))
    if not target:
        raise NotFoundError("User with that email not found — they must register first")
    exists = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target.id,
        )
    )
    if exists:
        raise ConflictError("User already in organization")
    db.add(OrganizationMember(organization_id=org_id, user_id=target.id, role=role))
    db.commit()
    return {"user_id": str(target.id), "email": target.email, "role": role}


def list_members(db: Session, user: User, org_id: UUID) -> list[dict]:
    _require_member(db, user, org_id)
    rows = list(
        db.scalars(select(OrganizationMember).where(OrganizationMember.organization_id == org_id)).all()
    )
    out = []
    for m in rows:
        u = db.get(User, m.user_id)
        out.append(
            {
                "user_id": str(m.user_id),
                "email": u.email if u else None,
                "full_name": u.full_name if u else None,
                "role": m.role,
            }
        )
    return out


def create_team(db: Session, user: User, org_id: UUID, *, name: str) -> Team:
    _require_member(db, user, org_id)
    if not name.strip():
        raise ValidationAppError("Team name is required")
    team = Team(organization_id=org_id, name=name.strip())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def list_teams(db: Session, user: User, org_id: UUID) -> list[dict]:
    _require_member(db, user, org_id)
    teams = list(db.scalars(select(Team).where(Team.organization_id == org_id)).all())
    return [{"id": str(t.id), "name": t.name, "organization_id": str(t.organization_id)} for t in teams]


def add_team_member(db: Session, user: User, team_id: UUID, *, email: str) -> dict:
    team = db.get(Team, team_id)
    if not team:
        raise NotFoundError("Team not found")
    _require_member(db, user, team.organization_id)
    target = db.scalar(select(User).where(User.email == email.lower()))
    if not target:
        raise NotFoundError("User not found")
    # must be org member
    org_m = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == team.organization_id,
            OrganizationMember.user_id == target.id,
        )
    )
    if not org_m:
        raise ValidationAppError("User must be an organization member first")
    exists = db.scalar(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == target.id)
    )
    if exists:
        raise ConflictError("Already on team")
    db.add(TeamMember(team_id=team_id, user_id=target.id))
    db.commit()
    return {"team_id": str(team_id), "user_id": str(target.id), "email": target.email}
