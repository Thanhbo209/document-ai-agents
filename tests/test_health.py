from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data == {
        "status": "ok",
        "app": "Rag Platform",
        "environment": "local",
        "version": "v1",
    }
