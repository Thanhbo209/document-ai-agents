from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Citation, ConversationMessage, UsageEvent
from app.limits.policies import WorkspaceLimitPolicy
from tests.helpers import create_authenticated_workspace


def create_workspace(db_session: Session) -> tuple[str, dict[str, str]]:
    return create_authenticated_workspace(
        db_session,
        email=f"phase15-{uuid4()}@example.com",
    )


def upload_text_document(
    client: TestClient,
    workspace_id: str,
    headers: dict[str, str],
    filename: str,
    content: bytes,
) -> str:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                filename,
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    return str(response.json()["document_id"])


def test_query_workspace_returns_grounded_answer_and_persists_conversation(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    upload_text_document(
        client=client,
        workspace_id=workspace_id,
        headers=headers,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert "Refund policy" in payload["message"]
    assert "[S1]" in payload["message"]
    assert len(payload["citations"]) == 1
    assert len(payload["source_list"]) >= 1
    assert payload["confidence"] > 0

    messages = list(db_session.scalars(select(ConversationMessage)).all())
    citations = list(db_session.scalars(select(Citation)).all())

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert len(citations) == 1


def test_query_workspace_records_usage_metrics(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    upload_text_document(
        client=client,
        workspace_id=workspace_id,
        headers=headers,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    payload = response.json()
    usage_events = list(
        db_session.scalars(
            select(UsageEvent)
            .where(
                UsageEvent.workspace_id == workspace_id,
                UsageEvent.source_type == "conversation",
            )
            .order_by(UsageEvent.metric_name)
        ).all()
    )
    usage_by_metric = {event.metric_name: event for event in usage_events}

    assert set(usage_by_metric) == {
        "llm.tokens",
        "query.count",
        "retrieval.results",
    }
    assert usage_by_metric["query.count"].quantity == 1
    assert usage_by_metric["query.count"].unit == "query"
    assert usage_by_metric["query.count"].usage_metadata == {
        "top_k": 3,
        "document_ids": [],
    }
    assert usage_by_metric["retrieval.results"].quantity == len(payload["source_list"])
    assert usage_by_metric["retrieval.results"].unit == "chunk"
    assert usage_by_metric["llm.tokens"].quantity == max(1, len(payload["message"].split()))
    assert usage_by_metric["llm.tokens"].unit == "token"
    assert usage_by_metric["llm.tokens"].usage_metadata == {
        "model_name": payload["model_name"],
        "prompt_id": payload["prompt_id"],
    }
    assert {event.source_id for event in usage_events} == {None}


def test_query_workspace_returns_429_when_quota_is_exceeded(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    monkeypatch.setattr(
        "app.limits.service.get_workspace_limit_policy",
        lambda: WorkspaceLimitPolicy(
            storage_bytes_limit=100 * 1024 * 1024,
            documents_limit=100,
            daily_query_limit=0,
            monthly_embedding_token_limit=500_000,
            monthly_llm_token_limit=500_000,
            concurrent_job_limit=2,
        ),
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "top_k": 5,
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"]["metric_name"] == "query.count"
    assert list(db_session.scalars(select(ConversationMessage)).all()) == []


def test_query_workspace_can_target_document_subset(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    refund_document_id = upload_text_document(
        client=client,
        workspace_id=workspace_id,
        headers=headers,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )
    shipping_document_id = upload_text_document(
        client=client,
        workspace_id=workspace_id,
        headers=headers,
        filename="shipping.txt",
        content=b"Shipping takes five business days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "document_ids": [shipping_document_id],
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["message"].startswith("I don't have enough evidence")
    assert payload["citations"] == []

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "document_ids": [refund_document_id],
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    assert "[S1]" in response.json()["message"]


def test_query_workspace_rejects_document_from_wrong_workspace(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_a, headers_a = create_workspace(db_session)
    workspace_b, headers_b = create_workspace(db_session)

    document_id = upload_text_document(
        client=client,
        workspace_id=workspace_b,
        headers=headers_b,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_a}/query",
        headers=headers_a,
        json={
            "query": "What is the refund policy?",
            "document_ids": [document_id],
        },
    )

    assert response.status_code == 404


def test_stream_query_workspace_returns_sse_events(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    upload_text_document(
        client=client,
        workspace_id=workspace_id,
        headers=headers,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    with client.stream(
        "POST",
        f"/api/v1/workspaces/{workspace_id}/query/stream",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "top_k": 5,
        },
    ) as response:
        assert response.status_code == 200
        body = response.read().decode()

    assert "event: start" in body
    assert "event: token" in body
    assert "event: final" in body
    assert "Refund" in body
