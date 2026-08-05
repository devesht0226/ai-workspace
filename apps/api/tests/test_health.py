"""Smoke tests for health endpoints."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_api_v1_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-workspace-api"


def test_normalize_database_url() -> None:
    from app.db.session import normalize_database_url

    assert normalize_database_url("postgres://u:p@h/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql://u:p@h/db").startswith("postgresql+psycopg://")
    assert (
        normalize_database_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    )
    assert normalize_database_url("sqlite:///./x.db") == "sqlite:///./x.db"


def test_cors_regex_for_vercel() -> None:
    from app.core.config import Settings

    s = Settings(
        environment="production",
        cors_origins="https://ai-workspace.vercel.app",
        app_base_url="https://ai-workspace.vercel.app",
        cors_origin_regex="",
    )
    assert s.resolved_cors_origin_regex is not None
    assert "vercel" in s.resolved_cors_origin_regex
    assert "https://ai-workspace.vercel.app" in s.cors_origins_list
