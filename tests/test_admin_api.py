import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.auth.security import hash_password
from app.db.models import User
from app.models.enums import JobStatus
from app.repositories.documents import DocumentRepository
from app.repositories.workspaces import WorkspaceRepository
from tests.helpers import auth_headers_for_user, create_authenticated_workspace


def create_platform_admin(db_session: Session) -> tuple[User, dict[str, str]]:
    repo = WorkspaceRepository(db_session)
    admin = repo.create_user(
        email="platform-admin@example.com",
        display_name="Platform Admin",
        password_hash=hash_password("password123"),
    )
    admin.is_platform_admin = True
    db_session.commit()

    return admin, auth_headers_for_user(admin.id, admin.email)


def test_admin_route_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/admin/workspaces")

    assert response.status_code == 401


def test_normal_user_cannot_access_admin_route(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)
    user = repo.create_user(
        email="normal-user@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/workspaces",
        headers=auth_headers_for_user(user.id, user.email),
    )

    assert response.status_code == 403


def test_platform_admin_can_list_workspaces(
    client: TestClient,
    db_session: Session,
) -> None:
    _, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="admin-visible-owner@example.com",
    )

    response = client.get(
        "/api/v1/admin/workspaces",
        headers=admin_headers,
    )

    assert response.status_code == 200

    workspaces = {workspace["id"]: workspace for workspace in response.json()}
    assert workspace_id in workspaces
    assert workspaces[workspace_id]["owner_email"] == "admin-visible-owner@example.com"
    assert workspaces[workspace_id]["plan_name"] == "free"


def test_platform_admin_can_inspect_failed_jobs(
    client: TestClient,
    db_session: Session,
) -> None:
    _, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="failed-job-owner@example.com",
    )
    document_repo = DocumentRepository(db_session)
    document = document_repo.create_document(
        workspace_id=workspace_id,
        title="Broken upload",
        source_type="pdf",
    )
    job = document_repo.create_ingestion_job(
        workspace_id=workspace_id,
        document_id=document.id,
        status=JobStatus.PROCESSING,
    )
    document_repo.update_ingestion_job_status(
        job,
        JobStatus.FAILED,
        error_message="PDF parser failed",
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/jobs",
        headers=admin_headers,
    )

    assert response.status_code == 200

    jobs = {job_payload["id"]: job_payload for job_payload in response.json()}
    assert job.id in jobs
    assert jobs[job.id]["status"] == "failed"
    assert jobs[job.id]["error_message"] == "PDF parser failed"


def test_platform_admin_can_filter_jobs_by_status(
    client: TestClient,
    db_session: Session,
) -> None:
    _, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="job-filter-owner@example.com",
    )
    document_repo = DocumentRepository(db_session)
    failed_document = document_repo.create_document(
        workspace_id=workspace_id,
        title="Failed",
        source_type="text",
    )
    queued_document = document_repo.create_document(
        workspace_id=workspace_id,
        title="Queued",
        source_type="text",
    )
    failed_job = document_repo.create_ingestion_job(
        workspace_id=workspace_id,
        document_id=failed_document.id,
        status=JobStatus.FAILED,
    )
    document_repo.create_ingestion_job(
        workspace_id=workspace_id,
        document_id=queued_document.id,
        status=JobStatus.QUEUED,
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/jobs",
        headers=admin_headers,
        params={"status": "failed"},
    )

    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [failed_job.id]


def test_platform_admin_can_search_audit_events(
    client: TestClient,
    db_session: Session,
) -> None:
    admin, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="audit-owner@example.com",
    )
    AuditEventRepository(db_session).record_event(
        workspace_id=workspace_id,
        actor_user_id=admin.id,
        event_type="support.lookup",
        entity_type="workspace",
        entity_id=workspace_id,
        payload={"reason": "operational review"},
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/audit-events",
        headers=admin_headers,
        params={"event_type": "support.lookup"},
    )

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "support.lookup"
    assert response.json()[0]["payload"] == {"reason": "operational review"}


def test_platform_admin_can_export_audit_events_as_csv(
    client: TestClient,
    db_session: Session,
) -> None:
    admin, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="csv-audit-owner@example.com",
    )
    AuditEventRepository(db_session).record_event(
        workspace_id=workspace_id,
        actor_user_id=admin.id,
        event_type="support.csv_export_test",
        entity_type="workspace",
        entity_id=workspace_id,
        payload={"scope": "csv"},
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/audit-events/export",
        headers=admin_headers,
        params={"format": "csv", "event_type": "support.csv_export_test"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "event_type" in response.text
    assert "support.csv_export_test" in response.text


def test_platform_admin_can_export_audit_events_as_json(
    client: TestClient,
    db_session: Session,
) -> None:
    admin, admin_headers = create_platform_admin(db_session)
    workspace_id, _ = create_authenticated_workspace(
        db_session,
        email="json-audit-owner@example.com",
    )
    AuditEventRepository(db_session).record_event(
        workspace_id=workspace_id,
        actor_user_id=admin.id,
        event_type="support.json_export_test",
        entity_type="workspace",
        entity_id=workspace_id,
        payload={"scope": "json"},
    )
    db_session.commit()

    response = client.get(
        "/api/v1/admin/audit-events/export",
        headers=admin_headers,
        params={"format": "json", "event_type": "support.json_export_test"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = json.loads(response.text)
    assert payload[0]["event_type"] == "support.json_export_test"
    assert payload[0]["payload"] == {"scope": "json"}


def test_admin_document_metadata_does_not_expose_raw_text_or_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    _, admin_headers = create_platform_admin(db_session)
    workspace_id, owner_headers = create_authenticated_workspace(
        db_session,
        email="private-doc-owner@example.com",
    )
    raw_private_text = "PRIVATE payroll note: Alice salary is confidential."

    upload_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents/upload",
        headers=owner_headers,
        files={
            "file": (
                "private-notes.md",
                raw_private_text.encode(),
                "text/markdown",
            )
        },
    )

    assert upload_response.status_code == 201

    response = client.get(
        f"/api/v1/admin/workspaces/{workspace_id}/documents",
        headers=admin_headers,
    )

    assert response.status_code == 200

    response_body = response.text
    response_payload = response.json()
    document = response_payload[0]

    assert document["title"] == "private-notes"
    assert document["file_count"] == 1
    assert document["chunk_count"] == 1
    assert "text" not in document
    assert "content" not in document
    assert '"text"' not in response_body
    assert '"content"' not in response_body
    assert raw_private_text not in response_body
    assert "Alice salary" not in response_body
