from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.db.models import AuditEvent, DocumentChunk, Workspace
from app.models.enums import WorkspaceRole, WorkspaceStatus
from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository
from tests.helpers import auth_headers_for_user, create_authenticated_workspace


def test_owner_can_export_workspace_data(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="compliance-export-owner@example.com",
    )

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "policy.txt",
                b"Private workspace owned policy text.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/compliance/export",
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["workspace"]["id"] == workspace_id
    assert payload["workspace"]["status"] == WorkspaceStatus.ACTIVE.value
    assert payload["documents"][0]["title"] == "policy"
    assert payload["chunks"][0]["text"] == "Private workspace owned policy text."


def test_workspace_export_creates_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="compliance-audit-owner@example.com",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/compliance/export",
        headers=headers,
    )

    assert response.status_code == 200

    events = list(
        db_session.scalars(select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)).all()
    )

    assert [event.event_type for event in events] == ["compliance.workspace_exported"]


def test_member_cannot_export_workspace_data(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)
    owner = repo.create_user(
        email="compliance-owner@example.com",
        password_hash=hash_password("password123"),
    )
    member = repo.create_user(
        email="compliance-member@example.com",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Compliance Workspace",
        owner_user_id=owner.id,
    )
    repo.add_member(
        workspace_id=workspace.id,
        user_id=member.id,
        role=WorkspaceRole.MEMBER,
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{workspace.id}/compliance/export",
        headers=auth_headers_for_user(member.id, member.email),
    )

    assert response.status_code == 403


def test_member_cannot_access_compliance_settings_or_delete_request(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)
    owner = repo.create_user(
        email="settings-owner-member-check@example.com",
        password_hash=hash_password("password123"),
    )
    member = repo.create_user(
        email="settings-member-check@example.com",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Owner Only Compliance",
        owner_user_id=owner.id,
    )
    repo.add_member(
        workspace_id=workspace.id,
        user_id=member.id,
        role=WorkspaceRole.MEMBER,
    )
    db_session.commit()

    headers = auth_headers_for_user(member.id, member.email)

    settings_response = client.get(
        f"/api/v1/workspaces/{workspace.id}/settings",
        headers=headers,
    )
    delete_response = client.post(
        f"/api/v1/workspaces/{workspace.id}/compliance/delete-request",
        headers=headers,
        json={"reason": "Member should not be able to request deletion"},
    )

    assert settings_response.status_code == 403
    assert delete_response.status_code == 403


def test_owner_can_request_workspace_deletion(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="delete-owner@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/delete-request",
        headers=headers,
        json={"reason": "No longer needed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == WorkspaceStatus.PENDING_DELETION.value

    workspace = db_session.get(Workspace, workspace_id)
    assert workspace is not None
    assert workspace.status == WorkspaceStatus.PENDING_DELETION.value
    assert workspace.deletion_requested_at is not None


def test_delete_request_creates_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="delete-audit-owner@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/delete-request",
        headers=headers,
        json={"reason": "Archive tenant"},
    )

    assert response.status_code == 200

    events = list(
        db_session.scalars(select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)).all()
    )

    assert [event.event_type for event in events] == ["compliance.workspace_deletion_requested"]
    assert events[0].payload == {"reason": "Archive tenant"}


def test_mark_deleted_creates_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="mark-deleted-audit-owner@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/mark-deleted",
        headers=headers,
    )

    assert response.status_code == 200

    events = list(
        db_session.scalars(select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)).all()
    )

    assert [event.event_type for event in events] == ["compliance.workspace_deleted"]


def test_pending_deletion_workspace_blocks_upload_and_query(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="blocked-owner@example.com",
    )

    delete_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/delete-request",
        headers=headers,
        json={"reason": "Close workspace"},
    )

    assert delete_response.status_code == 200

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "blocked.txt",
                b"This should not ingest.",
                "text/plain",
            )
        },
    )
    query_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/query",
        headers=headers,
        json={"query": "Can I still query?"},
    )

    assert upload_response.status_code == 403
    assert upload_response.json()["detail"] == "Workspace is pending deletion."
    assert query_response.status_code == 403
    assert query_response.json()["detail"] == "Workspace is pending deletion."


def test_deleted_workspace_blocks_normal_access_with_410(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="gone-owner@example.com",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/mark-deleted",
        headers=headers,
    )

    assert response.status_code == 200

    documents_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers=headers,
    )

    assert documents_response.status_code == 410
    assert documents_response.json()["detail"] == "Workspace has been deleted."


def test_workspace_settings_returns_lifecycle_status(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="settings-owner@example.com",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/settings",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["workspace_id"] == workspace_id
    assert response.json()["status"] == WorkspaceStatus.ACTIVE.value
    assert response.json()["plan"]["name"] == "free"


def test_soft_delete_does_not_remove_documents_or_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(
        db_session,
        email="soft-delete-owner@example.com",
    )

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=headers,
        files={
            "file": (
                "retained.txt",
                b"Retained after soft delete.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    delete_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/compliance/mark-deleted",
        headers=headers,
    )

    assert delete_response.status_code == 200

    document_count = len(DocumentRepository(db_session).list_documents_for_workspace(workspace_id))
    chunk_count = db_session.scalar(
        select(DocumentChunk).where(DocumentChunk.workspace_id == workspace_id)
    )

    assert document_count == 1
    assert chunk_count is not None


def test_admin_can_still_see_deleted_workspace_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)
    owner = repo.create_user(
        email="deleted-admin-owner@example.com",
        password_hash=hash_password("password123"),
    )
    admin = repo.create_user(
        email="deleted-admin@example.com",
        password_hash=hash_password("password123"),
    )
    admin.is_platform_admin = True
    workspace = repo.create_workspace(
        name="Deleted Admin Workspace",
        owner_user_id=owner.id,
    )
    workspace.status = WorkspaceStatus.DELETED.value
    db_session.commit()

    response = client.get(
        "/api/v1/admin/workspaces",
        headers=auth_headers_for_user(admin.id, admin.email),
    )

    assert response.status_code == 200

    workspaces = {item["id"]: item for item in response.json()}
    assert workspaces[workspace.id]["status"] == WorkspaceStatus.DELETED.value
