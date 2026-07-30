"""Versioned health endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-workspace-api"}
