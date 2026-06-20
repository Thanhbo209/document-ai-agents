from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Citation, ConversationMessage
from app.repositories.workspaces import WorkspaceRepository


def create_workspace(db_session: Session) -> str:
    workspace_repo = WorkspaceRepository(db_session)

    user = workspace_repo.create_user(
        email=f"phase15-{uuid4()}@example.com",
        display_name="Phase 15 User",
    )
    workspace = workspace_repo.create_workspace(
        name="Phase 15 Workspace",
        owner_user_id=user.id,
    )
    db_session.commit()

    return workspace.id


def upload_text_document(
    client: TestClient,
    workspace_id: str,
    filename: str,
    content: bytes,
) -> str:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
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
    workspace_id = create_workspace(db_session)
    upload_text_document(
        client=client,
        workspace_id=workspace_id,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
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


def test_query_workspace_can_target_document_subset(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id = create_workspace(db_session)
    refund_document_id = upload_text_document(
        client=client,
        workspace_id=workspace_id,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )
    shipping_document_id = upload_text_document(
        client=client,
        workspace_id=workspace_id,
        filename="shipping.txt",
        content=b"Shipping takes five business days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
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
    workspace_a = create_workspace(db_session)
    workspace_b = create_workspace(db_session)

    document_id = upload_text_document(
        client=client,
        workspace_id=workspace_b,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_a}/query",
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
    workspace_id = create_workspace(db_session)
    upload_text_document(
        client=client,
        workspace_id=workspace_id,
        filename="refund.txt",
        content=b"Refund policy allows cancellation within 14 days.",
    )

    with client.stream(
        "POST",
        f"/api/v1/workspaces/{workspace_id}/query/stream",
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
