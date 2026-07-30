"""Auth V1.1, metrics, admin, hybrid helpers."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import hash_token
from app.db import session as db_session
from app.models import User, UserRole
from app.services.hybrid_search import bm25_scores, rrf_fuse


def test_password_reset_flow(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/api/v1/auth/register",
        json={"email": "resetme@example.com", "password": "password123"},
    )
    req = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "resetme@example.com"},
    )
    assert req.status_code == 200

    assert db_session.SessionLocal is not None
    with db_session.SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "resetme@example.com"))
        assert user is not None
        raw = "test-reset-token-value-1234567890"
        user.password_reset_token_hash = hash_token(raw)
        from datetime import datetime, timedelta, timezone

        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(user)
        db.commit()

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw, "new_password": "newpassword99"},
    )
    assert confirm.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "newpassword99"},
    )
    assert login.status_code == 200


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "aiworkspace_up 1" in response.text


def test_admin_requires_admin(client: TestClient, auth_headers: dict[str, str]) -> None:
    denied = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert denied.status_code == 403

    assert db_session.SessionLocal is not None
    with db_session.SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "alex@example.com"))
        assert user is not None
        user.role = UserRole.admin
        db.add(user)
        db.commit()

    ok = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["users"] >= 1


def test_hybrid_helpers() -> None:
    scores = bm25_scores("uptime sla", ["uptime target 99.9", "unrelated cooking recipe"])
    assert scores[0] > scores[1]
    fused = rrf_fuse(["a", "b", "c"], ["b", "a"], top_k=2)
    assert fused[0] in {"a", "b"}
