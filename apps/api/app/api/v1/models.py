"""Model router API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.providers.llm import ChatMessage
from app.providers.router import get_model_router, reset_model_router

router = APIRouter(prefix="/models", tags=["models"])


class RouteChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    family: str | None = Field(default=None, max_length=40)


@router.get("/catalog")
def catalog(_: CurrentUser) -> dict:
    reset_model_router()
    return {
        "default_family": get_model_router().resolve_family(None),
        "models": get_model_router().available(),
        "gateway": "AI Workspace API Gateway (/api/v1)",
    }


@router.post("/chat")
def route_chat(payload: RouteChatRequest, _: CurrentUser) -> dict:
    reset_model_router()
    return get_model_router().chat(
        [ChatMessage(role="user", content=payload.prompt)],
        family=payload.family,
    )
