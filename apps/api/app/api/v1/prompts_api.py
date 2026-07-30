"""Prompt registry API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import prompts as prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20000)
    model_family: str | None = Field(default=None, max_length=40)
    performance_score: float | None = None


@router.get("")
def list_prompts(db: DbSession, name: str | None = None) -> dict:
    prompt_service.seed_defaults(db)
    rows = prompt_service.list_prompts(db, name=name)
    return {
        "prompts": [
            {
                "id": str(r.id),
                "name": r.name,
                "version": r.version,
                "content": r.content,
                "model_family": r.model_family,
                "created_by": r.created_by,
                "performance_score": r.performance_score,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.post("", status_code=201)
def create_prompt(payload: PromptCreate, db: DbSession, user: CurrentUser) -> dict:
    row = prompt_service.create_prompt_version(
        db,
        user,
        name=payload.name,
        content=payload.content,
        model_family=payload.model_family,
        performance_score=payload.performance_score,
    )
    return {
        "id": str(row.id),
        "name": row.name,
        "version": row.version,
        "is_active": row.is_active,
    }


@router.get("/active/{name}")
def get_active(name: str, db: DbSession) -> dict:
    row = prompt_service.get_active_prompt(db, name)
    return {
        "id": str(row.id),
        "name": row.name,
        "version": row.version,
        "content": row.content,
        "model_family": row.model_family,
        "is_active": row.is_active,
    }
