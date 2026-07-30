"""Organization and team routes."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import CurrentUser, DbSession
from app.services import orgs as org_service

router = APIRouter(prefix="/orgs", tags=["organizations"])


class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


@router.get("")
def list_orgs(db: DbSession, user: CurrentUser) -> dict:
    org_service.ensure_personal_org(db, user)
    return {"organizations": org_service.list_organizations(db, user)}


@router.post("", status_code=201)
def create_org(payload: OrgCreate, db: DbSession, user: CurrentUser) -> dict:
    org = org_service.create_organization(db, user, name=payload.name)
    return {"id": str(org.id), "name": org.name, "slug": org.slug}


@router.get("/{org_id}/members")
def members(org_id: UUID, db: DbSession, user: CurrentUser) -> dict:
    return {"members": org_service.list_members(db, user, org_id)}


@router.post("/{org_id}/members")
def invite(org_id: UUID, payload: MemberInvite, db: DbSession, user: CurrentUser) -> dict:
    return org_service.add_member(db, user, org_id, email=payload.email, role=payload.role)


@router.get("/{org_id}/teams")
def teams(org_id: UUID, db: DbSession, user: CurrentUser) -> dict:
    return {"teams": org_service.list_teams(db, user, org_id)}


@router.post("/{org_id}/teams", status_code=201)
def create_team(org_id: UUID, payload: TeamCreate, db: DbSession, user: CurrentUser) -> dict:
    team = org_service.create_team(db, user, org_id, name=payload.name)
    return {"id": str(team.id), "name": team.name}


@router.post("/teams/{team_id}/members")
def add_team_member(team_id: UUID, payload: MemberInvite, db: DbSession, user: CurrentUser) -> dict:
    return org_service.add_team_member(db, user, team_id, email=payload.email)
