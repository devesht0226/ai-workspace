#!/usr/bin/env python
"""API smoke E2E against a running server (default http://localhost:8000)."""

from __future__ import annotations

import os
import sys
import uuid

import httpx

BASE = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")


def main() -> int:
    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert "aiworkspace_up" in client.get("/metrics").text
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Smoke"},
        )
        reg.raise_for_status()
        login = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        login.raise_for_status()
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        chat = client.post("/api/v1/chats", headers=headers, json={"title": "Smoke"})
        chat.raise_for_status()
        schema = client.get("/api/v1/sql/schema", headers=headers)
        schema.raise_for_status()
        dash = client.get("/api/v1/dashboard/summary", headers=headers)
        dash.raise_for_status()
    print("E2E smoke OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"E2E smoke FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
