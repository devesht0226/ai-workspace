"""Production-grade platform: traces, RAG eval, feedback, prompts, benchmarks."""

from fastapi.testclient import TestClient

from app.services.rag_eval import (
    answer_relevance,
    evaluate_rag,
    faithfulness,
    hallucination_score,
    mrr,
    precision_at_k,
    recall_at_k,
)


def test_rag_eval_metrics_unit() -> None:
    retrieved = ["a", "b", "c", "d"]
    relevant = ["b", "c"]
    assert precision_at_k(relevant, retrieved, 2) == 0.5
    assert recall_at_k(relevant, retrieved, 3) == 1.0
    assert mrr(relevant, retrieved) == 0.5
    answer = "rag retrieves documents for grounded answers"
    contexts = ["Retrieval-Augmented Generation retrieves documents for grounded LLM answers"]
    assert faithfulness(answer, contexts) > 0
    assert answer_relevance("what is rag", answer) > 0
    assert 0 <= hallucination_score(answer, contexts) <= 1
    metrics = evaluate_rag(
        question="what is rag",
        answer=answer,
        contexts=contexts,
        retrieved_ids=retrieved,
        relevant_ids=relevant,
        citations=[{"snippet": contexts[0]}],
    )
    assert "overall" in metrics
    assert "faithfulness" in metrics


def test_traces_after_agent_run(client: TestClient, auth_headers: dict[str, str]) -> None:
    run = client.post(
        "/api/v1/agents/runs",
        headers=auth_headers,
        json={"task": "Research documents about SLA availability", "model_family": "llama"},
    )
    assert run.status_code == 201, run.text

    traces = client.get("/api/v1/traces", headers=auth_headers)
    assert traces.status_code == 200
    assert len(traces.json()["traces"]) >= 1
    trace_id = traces.json()["traces"][0]["id"]

    detail = client.get(f"/api/v1/traces/{trace_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "completed"
    assert len(body["steps"]) >= 2
    agents = {s["agent_name"] for s in body["steps"]}
    assert "planner" in agents
    assert "evaluation" in agents or "report" in agents


def test_feedback_loop(client: TestClient, auth_headers: dict[str, str]) -> None:
    good = client.post(
        "/api/v1/feedback",
        headers=auth_headers,
        json={
            "target_type": "chat",
            "rating": 1,
            "answer_snapshot": "Transformer uses attention.",
        },
    )
    assert good.status_code == 200

    bad = client.post(
        "/api/v1/feedback",
        headers=auth_headers,
        json={"target_type": "research", "rating": -1, "comment": "off topic"},
    )
    assert bad.status_code == 200

    summary = client.get("/api/v1/feedback/summary", headers=auth_headers)
    assert summary.status_code == 200
    assert summary.json()["good"] >= 1
    assert summary.json()["bad"] >= 1


def test_prompt_registry(client: TestClient, auth_headers: dict[str, str]) -> None:
    listed = client.get("/api/v1/prompts", headers=auth_headers)
    assert listed.status_code == 200
    names = {p["name"] for p in listed.json()["prompts"]}
    assert "rag_grounded" in names

    created = client.post(
        "/api/v1/prompts",
        headers=auth_headers,
        json={
            "name": "rag_grounded",
            "content": "You are an expert researcher. Cite every claim.",
            "model_family": "llama",
        },
    )
    assert created.status_code == 201
    assert created.json()["version"] >= 2

    active = client.get("/api/v1/prompts/active/rag_grounded", headers=auth_headers)
    assert active.status_code == 200
    assert "expert researcher" in active.json()["content"]


def test_eval_and_benchmark_apis(client: TestClient, auth_headers: dict[str, str]) -> None:
    score = client.post(
        "/api/v1/eval/rag/score",
        headers=auth_headers,
        json={
            "question": "What is RAG?",
            "answer": "RAG retrieves documents to ground answers.",
            "contexts": ["RAG retrieves relevant documents for grounded generation."],
            "retrieved_ids": ["c1", "c2"],
            "citations": [{"snippet": "RAG retrieves relevant documents"}],
        },
    )
    assert score.status_code == 200
    assert "faithfulness" in score.json()

    stored = client.post(
        "/api/v1/eval/rag",
        headers=auth_headers,
        json={
            "question": "What is RAG?",
            "answer": "RAG retrieves documents to ground answers.",
            "contexts": ["RAG retrieves relevant documents for grounded generation."],
            "retrieved_ids": ["c1"],
        },
    )
    assert stored.status_code == 200

    history = client.get("/api/v1/eval/rag", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()["evals"]) >= 1

    bench = client.post(
        "/api/v1/benchmarks",
        headers=auth_headers,
        json={"question": "What is a vector database?"},
    )
    assert bench.status_code == 200, bench.text
    assert isinstance(bench.json()["ranking"], list)
    assert len(bench.json()["results"]) >= 1
