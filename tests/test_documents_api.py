from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.documents import DocumentRepository
from tests.helpers import create_authenticated_workspace


def create_workspace(db_session: Session) -> tuple[str, dict[str, str]]:
    return create_authenticated_workspace(
        db_session,
        email="phase14@example.com",
    )


def test_list_workspace_documents_returns_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "notes.txt",
                b"Hello from Phase 14 upload manager.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=headers,
    )

    assert list_response.status_code == 200

    payload = list_response.json()

    assert payload["workspace_id"] == workspace_id
    assert payload["total"] == 1

    document = payload["documents"][0]

    assert document["title"] == "notes"
    assert document["source_type"] == "text"
    assert document["status"] == "indexed"
    assert document["chunk_count"] == 1
    assert len(document["files"]) == 1
    assert document["latest_job"]["status"] == "succeeded"


def test_list_workspace_documents_supports_search(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    document_repo = DocumentRepository(db_session)
    document_repo.create_document(
        workspace_id=workspace_id,
        title="Refund Policy",
        source_type="text",
    )
    document_repo.create_document(
        workspace_id=workspace_id,
        title="Shipping Guide",
        source_type="text",
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=headers,
        params={"query": "refund"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert payload["documents"][0]["title"] == "Refund Policy"


def test_list_workspace_documents_supports_status_filter(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    document_repo = DocumentRepository(db_session)
    document_repo.create_document(
        workspace_id=workspace_id,
        title="Indexed Doc",
        source_type="text",
    )
    document_repo.create_document(
        workspace_id=workspace_id,
        title="Failed Doc",
        source_type="pdf",
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=headers,
        params={"status": "created"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 2


def test_failed_upload_appears_with_job_error(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "broken.pdf",
                b"this is not a real pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=headers,
    )

    assert list_response.status_code == 200

    payload = list_response.json()
    document = payload["documents"][0]

    assert document["status"] == "failed"
    assert document["latest_job"]["status"] == "failed"
    assert document["latest_job"]["error_message"]
