"""Knowledge graph API."""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.services import knowledge_graph as kg

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.get("")
def get_graph(db: DbSession, user: CurrentUser, limit: int = Query(default=100, le=500)) -> dict:
    return kg.get_graph(db, user, limit=limit)


@router.get("/search")
def search_graph(q: str, db: DbSession, user: CurrentUser) -> dict:
    return kg.query_graph(db, user, q)
