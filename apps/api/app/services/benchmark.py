"""Model benchmarking: same question across Llama/GPT/Mistral."""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ModelBenchmark, User
from app.providers.llm import ChatMessage
from app.providers.router import get_model_router, reset_model_router
from app.services.rag_eval import answer_relevance, faithfulness


def run_benchmark(db: Session, user: User, question: str) -> ModelBenchmark:
    reset_model_router()
    router = get_model_router()
    results = []
    for family in ("llama", "gpt", "mistral"):
        start = time.perf_counter()
        available = any(m["family"] == family and m["available"] for m in router.available())
        if not available and family != "llama":
            # In fake/test mode all are available; otherwise skip missing keys
            if not any(m["family"] == family and m["available"] for m in router.available()):
                results.append(
                    {
                        "family": family,
                        "available": False,
                        "error": "API key not configured",
                        "latency_ms": 0,
                        "answer": None,
                        "scores": {},
                    }
                )
                continue
        try:
            routed = router.chat([ChatMessage(role="user", content=question)], family=family)
            answer = routed["content"]
            latency = int((time.perf_counter() - start) * 1000)
            # Lightweight offline scoring without gold contexts
            scores = {
                "answer_relevance": round(answer_relevance(question, answer), 4),
                "faithfulness_self": round(faithfulness(answer, [answer]), 4),
                "length": len(answer.split()),
                "latency_ms": latency,
            }
            # Composite: relevance high, latency low preference
            scores["composite"] = round(
                scores["answer_relevance"] * 0.7 + max(0, 1 - latency / 5000) * 0.3,
                4,
            )
            results.append(
                {
                    "family": family,
                    "available": True,
                    "answer": answer,
                    "latency_ms": latency,
                    "scores": scores,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "family": family,
                    "available": False,
                    "error": str(exc),
                    "latency_ms": int((time.perf_counter() - start) * 1000),
                    "answer": None,
                    "scores": {},
                }
            )

    ranked = sorted(
        [r for r in results if r.get("available") and r.get("scores")],
        key=lambda r: r["scores"].get("composite", 0),
        reverse=True,
    )
    ranking = [r["family"] for r in ranked]
    row = ModelBenchmark(
        user_id=user.id,
        question=question,
        results_json=results,
        ranking_json=ranking,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_benchmarks(db: Session, user: User, *, limit: int = 20) -> list[ModelBenchmark]:
    return list(
        db.scalars(
            select(ModelBenchmark)
            .where(ModelBenchmark.user_id == user.id)
            .order_by(ModelBenchmark.created_at.desc())
            .limit(limit)
        ).all()
    )
