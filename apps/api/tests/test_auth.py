"""Auth API tests."""

from fastapi.testclient import TestClient


def test_register_login_me(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "jordan@example.com",
            "password": "password123",
            "full_name": "Jordan",
        },
    )
    assert register.status_code == 201
    assert register.json()["email"] == "jordan@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "jordan@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert "access_token" in body
    assert "refresh_token" in body

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["full_name"] == "Jordan"


def test_refresh_and_logout(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "sam@example.com", "password": "password123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "sam@example.com", "password": "password123"},
    ).json()

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access}"},
        json={"refresh_token": refreshed.json()["refresh_token"]},
    )
    assert logout.status_code == 204


def test_duplicate_email(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    again = client.post("/api/v1/auth/register", json=payload)
    assert again.status_code == 409
