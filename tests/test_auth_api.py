from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_register_creates_user_workspace_and_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "display_name": "New User",
            "workspace_name": "New Workspace",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "new@example.com"
    assert payload["default_workspace_id"]
    assert payload["user"]["workspaces"][0]["role"] == "owner"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dupe@example.com",
        "password": "password123",
        "display_name": "Dupe",
        "workspace_name": "Dupe Workspace",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_login_returns_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "display_name": "Login User",
            "workspace_name": "Login Workspace",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "display_name": "Wrong User",
            "workspace_name": "Wrong Workspace",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "bad-password",
        },
    )

    assert response.status_code == 401


def test_me_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(
    client: TestClient,
    db_session: Session,
) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "display_name": "Me User",
            "workspace_name": "Me Workspace",
        },
    )

    token = register.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
