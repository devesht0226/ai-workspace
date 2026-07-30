"""Security polish tests."""

from fastapi.testclient import TestClient


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-request-id")


def test_rate_limit_when_enabled(client: TestClient, monkeypatch) -> None:
    from app.core import security_middleware as sm
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()
    sm._rate_buckets.clear()

    # Hit a non-health endpoint repeatedly
    codes = []
    for _ in range(5):
        codes.append(client.get("/api/v1/health").status_code)
    get_settings.cache_clear()
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    assert 429 in codes
