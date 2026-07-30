"""Chat API tests with fake LLM provider."""

from fastapi.testclient import TestClient


def test_chat_non_stream(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/chats", headers=auth_headers, json={"title": "Demo"})
    assert created.status_code == 201
    session_id = created.json()["id"]

    reply = client.post(
        f"/api/v1/chats/{session_id}/messages",
        headers=auth_headers,
        json={"content": "Hello workspace", "stream": False},
    )
    assert reply.status_code == 200
    assert "Echo:" in reply.json()["content"]

    detail = client.get(f"/api/v1/chats/{session_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2


def test_chat_stream(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/api/v1/chats", headers=auth_headers, json={})
    session_id = created.json()["id"]
    with client.stream(
        "POST",
        f"/api/v1/chats/{session_id}/messages",
        headers=auth_headers,
        json={"content": "Stream please", "stream": True},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    assert "token" in body
    assert "done" in body
