"""Blueprint gap coverage: orgs, notifications, nDCG, chat rename, GDPR."""

from fastapi.testclient import TestClient

from app.services.rag_eval import evaluate_rag, ndcg_at_k


def test_ndcg_metric() -> None:
    assert ndcg_at_k(["a", "b"], ["a", "x", "b"], 3) > 0
    metrics = evaluate_rag(
        question="what is rag",
        answer="rag retrieves documents",
        contexts=["rag retrieves documents for grounding"],
        retrieved_ids=["a", "b", "c"],
        relevant_ids=["a", "b"],
    )
    assert "ndcg_at_k" in metrics


def test_orgs_and_notifications(client: TestClient, auth_headers: dict[str, str]) -> None:
    orgs = client.get("/api/v1/orgs", headers=auth_headers)
    assert orgs.status_code == 200
    assert len(orgs.json()["organizations"]) >= 1

    created = client.post(
        "/api/v1/orgs",
        headers=auth_headers,
        json={"name": "Acme Research Lab"},
    )
    assert created.status_code == 201

    notes = client.get("/api/v1/notifications", headers=auth_headers)
    assert notes.status_code == 200
    assert "unread" in notes.json()


def test_chat_rename_and_sessions(client: TestClient, auth_headers: dict[str, str]) -> None:
    chat = client.post("/api/v1/chats", headers=auth_headers, json={"title": "Temp"})
    assert chat.status_code == 201
    cid = chat.json()["id"]
    renamed = client.patch(
        f"/api/v1/chats/{cid}",
        headers=auth_headers,
        json={"title": "Renamed chat"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Renamed chat"

    sessions = client.get("/api/v1/users/me/sessions", headers=auth_headers)
    assert sessions.status_code == 200
    assert isinstance(sessions.json()["sessions"], list)


def test_chat_export_and_delete(client: TestClient, auth_headers: dict[str, str]) -> None:
    chat = client.post("/api/v1/chats", headers=auth_headers, json={"title": "Export me"})
    assert chat.status_code == 201
    cid = chat.json()["id"]

    exported = client.get(f"/api/v1/chats/{cid}/export", headers=auth_headers)
    assert exported.status_code == 200
    assert "Export me" in exported.text or "chat" in exported.text.lower()

    deleted = client.delete(f"/api/v1/chats/{cid}", headers=auth_headers)
    assert deleted.status_code == 204
    missing = client.get(f"/api/v1/chats/{cid}", headers=auth_headers)
    assert missing.status_code == 404


def test_gdpr_export(client: TestClient, auth_headers: dict[str, str]) -> None:
    exported = client.get("/api/v1/users/me/export", headers=auth_headers)
    assert exported.status_code == 200
    body = exported.json()
    assert "user" in body
    assert "chats" in body
    assert "documents" in body
    assert body["user"]["email"]


def test_txt_document_upload(client: TestClient, auth_headers: dict[str, str]) -> None:
    upload = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={
            "file": ("notes.txt", b"RAG retrieves documents for grounded answers.", "text/plain")
        },
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["status"] in {"ready", "processing", "failed", "pending"}


def test_change_password_and_logout_all(client: TestClient, auth_headers: dict[str, str]) -> None:
    bad = client.post(
        "/api/v1/users/me/change-password",
        headers=auth_headers,
        json={"current_password": "wrong-password", "new_password": "password456"},
    )
    assert bad.status_code in {401, 400, 422}

    ok = client.post(
        "/api/v1/auth/logout-all",
        headers=auth_headers,
    )
    assert ok.status_code == 200
    assert ok.json()["revoked"] >= 1
