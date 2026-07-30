"""Hybrid search helpers (BM25 + vector fusion)."""

from __future__ import annotations

import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_scores(
    query: str,
    documents: list[str],
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    if not documents:
        return []
    tokenized = [_tokenize(doc) for doc in documents]
    q_tokens = _tokenize(query)
    if not q_tokens:
        return [0.0] * len(documents)

    doc_lens = [len(tokens) or 1 for tokens in tokenized]
    avgdl = sum(doc_lens) / len(doc_lens)
    df: Counter[str] = Counter()
    for tokens in tokenized:
        df.update(set(tokens))

    n = len(documents)
    scores: list[float] = []
    for tokens, dl in zip(tokenized, doc_lens, strict=True):
        tf = Counter(tokens)
        score = 0.0
        for term in q_tokens:
            if term not in tf:
                continue
            n_q = df[term]
            idf = math.log(1 + (n - n_q + 0.5) / (n_q + 0.5))
            freq = tf[term]
            score += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / avgdl))
        scores.append(score)
    return scores


def rrf_fuse(
    vector_ranked_ids: list[str],
    bm25_ranked_ids: list[str],
    *,
    k: int = 60,
    top_k: int = 5,
) -> list[str]:
    scores: dict[str, float] = {}
    for rank, doc_id in enumerate(vector_ranked_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    for rank, doc_id in enumerate(bm25_ranked_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [doc_id for doc_id, _ in ordered[:top_k]]
