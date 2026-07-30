"""In-memory vector store used when Qdrant is unavailable (tests / offline)."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field


@dataclass
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict


@dataclass
class InMemoryVectorStore:
    points: dict[str, VectorPoint] = field(default_factory=dict)

    def upsert(self, points: list[VectorPoint]) -> None:
        for point in points:
            self.points[point.id] = point

    def delete_by_document(self, document_id: str) -> None:
        to_delete = [
            pid
            for pid, point in self.points.items()
            if str(point.payload.get("document_id")) == document_id
        ]
        for pid in to_delete:
            del self.points[pid]

    def search(
        self,
        vector: list[float],
        *,
        user_id: str,
        document_id: str | None = None,
        collection_id: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[VectorPoint, float]]:
        scored: list[tuple[VectorPoint, float]] = []
        for point in self.points.values():
            if str(point.payload.get("user_id")) != user_id:
                continue
            if document_id and str(point.payload.get("document_id")) != document_id:
                continue
            if collection_id and str(point.payload.get("collection_id")) != collection_id:
                continue
            score = _cosine(vector, point.vector)
            scored.append((point, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_GLOBAL_STORE = InMemoryVectorStore()


def get_memory_store() -> InMemoryVectorStore:
    return _GLOBAL_STORE


def new_point_id() -> str:
    return str(uuid.uuid4())
