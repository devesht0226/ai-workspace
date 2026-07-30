"""Advanced RAG evaluation API."""

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import rag_eval

router = APIRouter(prefix="/eval", tags=["evaluation"])


class RagEvalRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1, max_length=20000)
    contexts: list[str] = Field(default_factory=list)
    retrieved_ids: list[str] = Field(default_factory=list)
    relevant_ids: list[str] | None = None
    citations: list[dict] = Field(default_factory=list)
    k: int = Field(default=5, ge=1, le=50)


@router.post("/rag")
def evaluate_rag(payload: RagEvalRequest, db: DbSession, user: CurrentUser) -> dict:
    row = rag_eval.run_and_store_eval(
        db,
        user,
        question=payload.question,
        answer=payload.answer,
        contexts=payload.contexts,
        retrieved_ids=payload.retrieved_ids,
        relevant_ids=payload.relevant_ids,
        citations=payload.citations,
        k=payload.k,
    )
    return {
        "id": str(row.id),
        "question": row.question,
        "answer": row.answer,
        "metrics": row.metrics_json,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/rag")
def list_rag_evals(db: DbSession, user: CurrentUser, limit: int = 50) -> dict:
    rows = rag_eval.list_evals(db, user, limit=min(limit, 100))
    return {
        "evals": [
            {
                "id": str(r.id),
                "question": r.question,
                "answer": r.answer[:500],
                "metrics": r.metrics_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.get("/rag/{eval_id}/report")
def evaluation_report(eval_id: UUID, db: DbSession, user: CurrentUser) -> PlainTextResponse:
    row = rag_eval.get_eval(db, user, eval_id)
    return PlainTextResponse(rag_eval.report_markdown(row), media_type="text/markdown")


@router.post("/rag/score")
def score_only(payload: RagEvalRequest) -> dict:
    """Compute metrics without persistence (useful for research notebooks)."""
    return rag_eval.evaluate_rag(
        question=payload.question,
        answer=payload.answer,
        contexts=payload.contexts,
        retrieved_ids=payload.retrieved_ids,
        relevant_ids=payload.relevant_ids,
        citations=payload.citations,
        k=payload.k,
    )
