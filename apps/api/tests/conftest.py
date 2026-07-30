"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Must set before app imports that read settings/engine.
os.environ["ENVIRONMENT"] = "test"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-32b!"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import session as db_session
from app.db.session import Base, configure_engine, init_db
from app.main import app
from app.providers.vector_store import get_memory_store


@pytest.fixture(autouse=True)
def _reset_db(tmp_path):
    get_settings.cache_clear()
    os.environ["UPLOAD_DIR"] = str(tmp_path / "uploads")
    get_settings.cache_clear()
    configure_engine("sqlite:///:memory:")
    init_db()
    get_memory_store().points.clear()
    yield
    get_memory_store().points.clear()
    if db_session.engine is not None:
        Base.metadata.drop_all(bind=db_session.engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "alex@example.com",
            "password": "password123",
            "full_name": "Alex Chen",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
