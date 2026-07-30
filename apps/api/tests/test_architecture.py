"""Architecture completeness: model router, KG, memory, research."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.providers.router import ModelRouter, reset_model_router
from app.services.hybrid_search import bm25_scores
from app.services.knowledge_graph import extract_entities


def test_model_catalog(client: TestClient, auth_headers: dict[str, str]) -> None:
    reset_model_router()
    response = client.get("/api/v1/models/catalog", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    families = {m["family"] for m in body["models"]}
    assert {"llama", "gpt", "mistral"} <= families


def test_model_router_chat(client: TestClient, auth_headers: dict[str, str]) -> None:
    reset_model_router()
    response = client.post(
        "/api/v1/models/chat",
        headers=auth_headers,
        json={"prompt": "hello router", "family": "llama"},
    )
    assert response.status_code == 200
    assert response.json()["family"] == "llama"
    assert "Echo:" in response.json()["content"] or response.json()["content"]


def test_memory_and_research(client: TestClient, auth_headers: dict[str, str]) -> None:
    mem = client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"content": "Prefer PostgreSQL for analytics", "importance": 3},
    )
    assert mem.status_code == 200

    recall = client.get("/api/v1/memory/recall", headers=auth_headers, params={"q": "PostgreSQL"})
    assert recall.status_code == 200
    assert len(recall.json()["hits"]) >= 1

    research = client.post(
        "/api/v1/research",
        headers=auth_headers,
        json={"question": "What do we know about PostgreSQL?", "model_family": "llama"},
    )
    assert research.status_code == 200
    assert research.json()["agent"] == "research"
    assert research.json()["brief"]


def test_knowledge_graph_after_upload(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_pages = [(1, "Acme Corp Availability SLA uses PostgreSQL and Docker.")]
    with patch("app.services.documents._extract_pdf", return_value=(fake_pages, 1)):
        upload = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            files={"file": ("policy.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
    assert upload.status_code == 201, upload.text

    graph = client.get("/api/v1/knowledge-graph", headers=auth_headers)
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) >= 1


def test_agent_research_path(client: TestClient, auth_headers: dict[str, str]) -> None:
    run = client.post(
        "/api/v1/agents/runs",
        headers=auth_headers,
        json={"task": "Research availability SLA in our knowledge base", "model_family": "llama"},
    )
    assert run.status_code == 201, run.text
    agents = [s.get("agent") for s in run.json()["steps_json"]]
    assert "research" in agents or "rag" in agents or "retrieval" in agents
    assert "knowledge_graph" in agents
    assert "evaluation" in agents


def test_entity_extraction_and_router_unit() -> None:
    ents = extract_entities("FastAPI and PostgreSQL power Acme Workspace")
    assert any("PostgreSQL" in e or "FastAPI" in e or "Acme" in e for e in ents)
    assert bm25_scores("a", ["a b", "c"])[0] >= bm25_scores("a", ["a b", "c"])[1]
    router = ModelRouter()
    assert router.resolve_family("gpt") == "gpt"
    assert router.resolve_family("ollama") == "llama"
