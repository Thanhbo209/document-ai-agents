from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data == {
        "status": "ok",
        "service": "rag-platform-api",
        "environment": "local",
        "version": "v1",
    }


def test_readiness_check_returns_ready(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
    }


def test_metrics_returns_prometheus_text(client: TestClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "rag_platform_requests_total" in response.text
    assert "rag_platform_requests_failed_total" in response.text
    assert "rag_platform_uploads_total" in response.text
    assert "rag_platform_queries_total" in response.text


def test_request_id_header_is_returned(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"
