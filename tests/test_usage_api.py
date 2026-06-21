from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import create_authenticated_workspace


def test_usage_summary_requires_auth(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, _ = create_authenticated_workspace(db_session)

    response = client.get(f"/api/v1/workspaces/{workspace_id}/usage")

    assert response.status_code == 401


def test_usage_summary_returns_workspace_metrics(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/usage",
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["workspace_id"] == workspace_id
    assert payload["plan"] == {
        "name": "free",
        "display_name": "Free",
        "status": "active",
    }

    metric_names = {metric["metric_name"] for metric in payload["metrics"]}

    assert "storage.bytes" in metric_names
    assert "documents.count" in metric_names
    assert "query.count.daily" in metric_names
    assert "llm.tokens.monthly" in metric_names


def test_upload_records_usage_events(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "usage.txt",
                b"Refund policy allows cancellation within 14 days.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    usage_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/usage",
        headers=headers,
    )

    assert usage_response.status_code == 200

    metrics = {metric["metric_name"]: metric for metric in usage_response.json()["metrics"]}

    assert metrics["storage.bytes"]["current"] > 0
    assert metrics["documents.count"]["current"] == 1
    assert metrics["chunk.tokens.monthly"]["current"] > 0


def test_query_records_usage_events(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "refund.txt",
                b"Refund policy allows cancellation within 14 days.",
                "text/plain",
            )
        },
    )

    query_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "top_k": 5,
        },
    )

    assert query_response.status_code == 200

    usage_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/usage",
        headers=headers,
    )

    metrics = {metric["metric_name"]: metric for metric in usage_response.json()["metrics"]}

    assert metrics["query.count.daily"]["current"] == 1
    assert metrics["llm.tokens.monthly"]["current"] > 0
