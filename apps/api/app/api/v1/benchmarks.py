"""Model benchmarking API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import benchmark as benchmark_service

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


class BenchmarkRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


@router.post("")
def run_benchmark(payload: BenchmarkRequest, db: DbSession, user: CurrentUser) -> dict:
    row = benchmark_service.run_benchmark(db, user, payload.question)
    return {
        "id": str(row.id),
        "question": row.question,
        "results": row.results_json,
        "ranking": row.ranking_json,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("")
def list_benchmarks(db: DbSession, user: CurrentUser, limit: int = 20) -> dict:
    rows = benchmark_service.list_benchmarks(db, user, limit=min(limit, 50))
    return {
        "benchmarks": [
            {
                "id": str(r.id),
                "question": r.question,
                "results": r.results_json,
                "ranking": r.ranking_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
