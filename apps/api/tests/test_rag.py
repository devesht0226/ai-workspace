"""RAG ingest/query tests with fake embeddings/LLM and in-memory vectors."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_upload_and_query(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_pages = [(1, "Availability shall be maintained at 99.9 percent monthly uptime.")]

    with patch("app.services.documents._extract_pdf", return_value=(fake_pages, 1)):
        upload = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            files={"file": ("sla.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert upload.status_code == 201, upload.text
    doc = upload.json()
    assert doc["status"] == "ready"
    document_id = doc["id"]

    query = client.post(
        f"/api/v1/documents/{document_id}/query",
        headers=auth_headers,
        json={"question": "What is the uptime target?", "top_k": 3},
    )
    assert query.status_code == 200, query.text
    body = query.json()
    assert "answer" in body
    assert isinstance(body["citations"], list)
    assert len(body["citations"]) >= 1
