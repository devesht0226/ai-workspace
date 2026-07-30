"""Advanced RAG evaluation framework."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RagEvalRun, User
from app.schemas import CitationOut


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def precision_at_k(relevant: Iterable[str], retrieved: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = retrieved[:k]
    if not top:
        return 0.0
    rel = set(relevant)
    hits = sum(1 for doc in top if doc in rel)
    return hits / len(top)


def recall_at_k(relevant: Iterable[str], retrieved: list[str], k: int) -> float:
    rel = list(relevant)
    if not rel:
        return 0.0
    top = set(retrieved[:k])
    hits = sum(1 for doc in rel if doc in top)
    return hits / len(rel)


def mrr(relevant: Iterable[str], retrieved: list[str]) -> float:
    rel = set(relevant)
    for idx, doc in enumerate(retrieved, start=1):
        if doc in rel:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(relevant_ids: Iterable[str], retrieved_ids: list[str], k: int) -> float:
    """Compute normalized discounted cumulative gain with binary relevance."""
    if k <= 0:
        return 0.0
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    dcg = sum(
        1.0 / math.log2(index + 1)
        for index, item_id in enumerate(retrieved_ids[:k], start=1)
        if item_id in relevant
    )
    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def context_relevance(question: str, contexts: list[str]) -> float:
    q = _tokenize(question)
    if not q or not contexts:
        return 0.0
    scores = []
    for ctx in contexts:
        c = _tokenize(ctx)
        scores.append(len(q & c) / len(q))
    return sum(scores) / len(scores)


def faithfulness(answer: str, contexts: list[str]) -> float:
    a = _tokenize(answer)
    if not a:
        return 0.0
    ctx = set().union(*(_tokenize(c) for c in contexts)) if contexts else set()
    if not ctx:
        return 0.0
    return len(a & ctx) / len(a)


def answer_relevance(question: str, answer: str) -> float:
    q = _tokenize(question)
    a = _tokenize(answer)
    if not q or not a:
        return 0.0
    return len(q & a) / len(q)


def hallucination_score(answer: str, contexts: list[str]) -> float:
    # Inverse of faithfulness (unsupported tokens ratio)
    return max(0.0, 1.0 - faithfulness(answer, contexts))


def citation_correctness(answer: str, citations: list[CitationOut] | list[dict]) -> float:
    if not citations:
        return 0.0 if answer.strip() else 1.0
    snippets = []
    for c in citations:
        if isinstance(c, dict):
            snippets.append(str(c.get("snippet") or ""))
        else:
            snippets.append(c.snippet or "")
    # Fraction of citations that share tokens with the answer
    a = _tokenize(answer)
    if not a:
        return 0.0
    good = 0
    for snip in snippets:
        if _tokenize(snip) & a:
            good += 1
    return good / len(snippets)


def evaluate_rag(
    *,
    question: str,
    answer: str,
    contexts: list[str],
    retrieved_ids: list[str],
    relevant_ids: list[str] | None = None,
    citations: list | None = None,
    k: int = 5,
) -> dict:
    relevant = relevant_ids or retrieved_ids[: max(1, min(3, len(retrieved_ids)))]
    metrics = {
        "precision_at_k": round(precision_at_k(relevant, retrieved_ids, k), 4),
        "recall_at_k": round(recall_at_k(relevant, retrieved_ids, k), 4),
        "mrr": round(mrr(relevant, retrieved_ids), 4),
        "ndcg_at_k": round(ndcg_at_k(relevant, retrieved_ids, k), 4),
        "context_relevance": round(context_relevance(question, contexts), 4),
        "faithfulness": round(faithfulness(answer, contexts), 4),
        "answer_relevance": round(answer_relevance(question, answer), 4),
        "hallucination_score": round(hallucination_score(answer, contexts), 4),
        "citation_correctness": round(citation_correctness(answer, citations or []), 4),
        "k": k,
    }
    metrics["overall"] = round(
        (
            metrics["context_relevance"]
            + metrics["faithfulness"]
            + metrics["answer_relevance"]
            + (1.0 - metrics["hallucination_score"])
            + metrics["citation_correctness"]
        )
        / 5.0,
        4,
    )
    return metrics


def run_and_store_eval(
    db: Session,
    user: User,
    *,
    question: str,
    answer: str,
    contexts: list[str],
    retrieved_ids: list[str],
    relevant_ids: list[str] | None = None,
    citations: list | None = None,
    k: int = 5,
) -> RagEvalRun:
    metrics = evaluate_rag(
        question=question,
        answer=answer,
        contexts=contexts,
        retrieved_ids=retrieved_ids,
        relevant_ids=relevant_ids,
        citations=citations,
        k=k,
    )
    row = RagEvalRun(
        user_id=user.id,
        question=question,
        answer=answer,
        metrics_json=metrics,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_evals(db: Session, user: User, *, limit: int = 50) -> list[RagEvalRun]:
    return list(
        db.scalars(
            select(RagEvalRun)
            .where(RagEvalRun.user_id == user.id)
            .order_by(RagEvalRun.created_at.desc())
            .limit(limit)
        ).all()
    )


def get_eval(db: Session, user: User, eval_id) -> RagEvalRun:
    row = db.scalar(select(RagEvalRun).where(RagEvalRun.id == eval_id, RagEvalRun.user_id == user.id))
    if row is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("RAG evaluation not found")
    return row


def report_markdown(eval_run: RagEvalRun) -> str:
    metrics = eval_run.metrics_json or {}
    metric_lines = "\n".join(
        f"- **{name.replace('_', ' ')}**: {value}" for name, value in metrics.items()
    )
    return (
        "# RAG Evaluation Report\n\n"
        f"## Question\n{eval_run.question}\n\n"
        f"## Answer\n{eval_run.answer}\n\n"
        f"## Metrics\n{metric_lines}\n"
    )
