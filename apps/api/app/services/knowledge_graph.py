"""Knowledge graph: entities and relations extracted from workspace content."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, KnowledgeEdge, KnowledgeNode, User

_ENTITY_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")
_STOP = {
    "The",
    "This",
    "That",
    "With",
    "From",
    "Your",
    "Our",
    "And",
    "For",
    "Availability",
}


def _upsert_node(
    db: Session, user: User, *, name: str, node_type: str, props: dict | None = None
) -> KnowledgeNode:
    existing = db.scalar(
        select(KnowledgeNode).where(
            KnowledgeNode.user_id == user.id,
            KnowledgeNode.name == name,
            KnowledgeNode.node_type == node_type,
        )
    )
    if existing:
        return existing
    node = KnowledgeNode(
        user_id=user.id,
        name=name,
        node_type=node_type,
        properties_json=props or {},
    )
    db.add(node)
    db.flush()
    return node


def _add_edge(
    db: Session,
    user: User,
    *,
    source: KnowledgeNode,
    target: KnowledgeNode,
    relation: str,
) -> None:
    existing = db.scalar(
        select(KnowledgeEdge).where(
            KnowledgeEdge.user_id == user.id,
            KnowledgeEdge.source_id == source.id,
            KnowledgeEdge.target_id == target.id,
            KnowledgeEdge.relation == relation,
        )
    )
    if existing:
        existing.weight += 1
        db.add(existing)
        return
    db.add(
        KnowledgeEdge(
            user_id=user.id,
            source_id=source.id,
            target_id=target.id,
            relation=relation,
            weight=1,
        )
    )


def extract_entities(text: str, *, limit: int = 20) -> list[str]:
    found: list[str] = []
    for match in _ENTITY_RE.findall(text or ""):
        name = match.strip()
        if name in _STOP or len(name) < 3:
            continue
        if name not in found:
            found.append(name)
        if len(found) >= limit:
            break
    # Also pull quoted tech-ish tokens
    for token in re.findall(r"\b([A-Za-z][A-Za-z0-9+.#-]{2,})\b", text or ""):
        lower = token.lower()
        if lower in {
            "python",
            "fastapi",
            "postgresql",
            "docker",
            "kubernetes",
            "react",
            "ollama",
            "qdrant",
            "rag",
            "sql",
        }:
            if token not in found:
                found.append(token)
    return found[:limit]


def ingest_document_graph(db: Session, user: User, document: Document, text: str) -> dict:
    doc_node = _upsert_node(
        db,
        user,
        name=document.filename,
        node_type="document",
        props={"document_id": str(document.id)},
    )
    entities = extract_entities(text)
    for name in entities:
        ent = _upsert_node(db, user, name=name, node_type="entity")
        _add_edge(db, user, source=doc_node, target=ent, relation="mentions")
        # Link co-occurring entities lightly
    for i, left in enumerate(entities[:8]):
        for right in entities[i + 1 : i + 3]:
            a = _upsert_node(db, user, name=left, node_type="entity")
            b = _upsert_node(db, user, name=right, node_type="entity")
            _add_edge(db, user, source=a, target=b, relation="related_to")
    db.commit()
    return {"document": document.filename, "entities": entities, "nodes_linked": len(entities)}


def get_graph(db: Session, user: User, *, limit: int = 100) -> dict:
    nodes = list(
        db.scalars(
            select(KnowledgeNode)
            .where(KnowledgeNode.user_id == user.id)
            .order_by(KnowledgeNode.created_at.desc())
            .limit(limit)
        ).all()
    )
    node_ids = {n.id for n in nodes}
    edges = list(
        db.scalars(
            select(KnowledgeEdge)
            .where(KnowledgeEdge.user_id == user.id)
            .order_by(KnowledgeEdge.created_at.desc())
            .limit(limit * 2)
        ).all()
    )
    return {
        "nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "type": n.node_type,
                "properties": n.properties_json or {},
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": str(e.id),
                "source": str(e.source_id),
                "target": str(e.target_id),
                "relation": e.relation,
                "weight": e.weight,
            }
            for e in edges
            if e.source_id in node_ids and e.target_id in node_ids
        ],
    }


def query_graph(db: Session, user: User, term: str) -> dict:
    nodes = list(
        db.scalars(
            select(KnowledgeNode).where(
                KnowledgeNode.user_id == user.id,
                KnowledgeNode.name.ilike(f"%{term}%"),
            )
        ).all()
    )
    related = []
    for node in nodes[:10]:
        edges = list(
            db.scalars(
                select(KnowledgeEdge).where(
                    KnowledgeEdge.user_id == user.id,
                    (KnowledgeEdge.source_id == node.id) | (KnowledgeEdge.target_id == node.id),
                )
            ).all()
        )
        related.append({"node": node.name, "type": node.node_type, "edge_count": len(edges)})
    return {"query": term, "matches": related}
