from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import create_authenticated_workspace


def create_workspace(db_session: Session) -> tuple[str, dict[str, str]]:
    return create_authenticated_workspace(
        db_session,
        email=f"chat-session-{uuid4()}@example.com",
    )


def upload_text_document(
    client: TestClient,
    workspace_id: str,
    headers: dict[str, str],
    filename: str = "refund.txt",
) -> str:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                filename,
                b"Refund policy allows cancellation within 14 days.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    return str(response.json()["document_id"])


def test_owner_can_create_and_list_chat_sessions(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions",
        headers=headers,
        json={"title": "Contract questions"},
    )

    assert create_response.status_code == 201
    session = create_response.json()
    assert session["title"] == "Contract questions"
    assert session["message_count"] == 0

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions",
        headers=headers,
    )

    assert list_response.status_code == 200
    sessions = list_response.json()
    assert [item["id"] for item in sessions] == [session["id"]]


def test_query_creates_chat_session_and_message_history(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    document_id = upload_text_document(client, workspace_id, headers)

    query_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "query": "What is the refund policy?",
            "document_ids": [document_id],
            "top_k": 5,
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()
    session_id = payload["chat_session_id"]
    assert payload["chat_session_title"] == "What is the refund policy?"

    messages_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions/{session_id}/messages",
        headers=headers,
    )

    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["attached_document_ids"] == [document_id]
    assert messages[1]["role"] == "assistant"
    assert messages[1]["citations"]
    assert messages[1]["source_list"]


def test_query_can_append_to_existing_chat_session(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)
    upload_text_document(client, workspace_id, headers)

    create_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions",
        headers=headers,
        json={"title": "New chat"},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    query_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={
            "chat_session_id": session_id,
            "query": "What is the refund policy?",
            "top_k": 5,
        },
    )

    assert query_response.status_code == 200
    assert query_response.json()["chat_session_id"] == session_id

    messages_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions/{session_id}/messages",
        headers=headers,
    )

    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 2


def test_missing_chat_session_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/chat-sessions/{uuid4()}/messages",
        headers=headers,
    )

    assert response.status_code == 404
