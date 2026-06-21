from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.db.models import AuditEvent
from app.repositories.workspaces import WorkspaceRepository
from tests.helpers import auth_headers_for_user


def create_workspace(db_session: Session) -> tuple[str, str, dict[str, str]]:
    workspace_repo = WorkspaceRepository(db_session)
    user = workspace_repo.create_user(
        email="reviewer@example.com",
        display_name="Reviewer",
        password_hash=hash_password("password123"),
    )
    workspace = workspace_repo.create_workspace(
        name="Review Workspace",
        owner_user_id=user.id,
    )
    db_session.commit()
    return user.id, workspace.id, auth_headers_for_user(user.id, user.email)


def create_review_item(
    client: TestClient,
    workspace_id: str,
    headers: dict[str, str],
) -> str:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items",
        headers=headers,
        json={
            "target_type": "extracted_field",
            "target_id": "field-1",
            "field_name": "renewal_date",
            "original_value": {"value": "2026-07-01"},
            "evidence": {
                "source_id": "S1",
                "quote": "Renewal date: 2026-07-01.",
            },
        },
    )

    assert response.status_code == 201
    return str(response.json()["id"])


def test_create_and_list_review_items(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    review_item_id = create_review_item(client, workspace_id, headers)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/review-items",
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["id"] == review_item_id
    assert payload[0]["status"] == "pending"


def test_approve_review_item_retains_reviewer_and_timestamp(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    review_item_id = create_review_item(client, workspace_id, headers)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items/{review_item_id}/approve",
        headers=headers,
        json={
            "reviewer_user_id": "reviewer-1",
            "reviewed_value": {"value": "2026-07-01"},
            "comments": "Looks correct.",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "approved"
    assert payload["reviewer_user_id"] == "reviewer-1"
    assert payload["reviewed_at"] is not None
    assert payload["comments"] == "Looks correct."

    events = list(db_session.scalars(select(AuditEvent)).all())

    assert [event.event_type for event in events] == [
        "review_item.created",
        "review_item.approved",
    ]


def test_approve_review_item_defaults_to_authenticated_user(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id, workspace_id, headers = create_workspace(db_session)
    review_item_id = create_review_item(client, workspace_id, headers)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items/{review_item_id}/approve",
        headers=headers,
        json={"reviewed_value": {"value": "2026-07-01"}},
    )

    assert response.status_code == 200
    assert response.json()["reviewer_user_id"] == user_id


def test_reject_review_item(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    review_item_id = create_review_item(client, workspace_id, headers)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items/{review_item_id}/reject",
        headers=headers,
        json={
            "reviewer_user_id": "reviewer-1",
            "comments": "Evidence does not support the value.",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "rejected"
    assert payload["reviewer_user_id"] == "reviewer-1"
    assert payload["reviewed_at"] is not None


def test_review_item_cannot_be_approved_twice(
    client: TestClient,
    db_session: Session,
) -> None:
    _user_id, workspace_id, headers = create_workspace(db_session)
    review_item_id = create_review_item(client, workspace_id, headers)

    first = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items/{review_item_id}/approve",
        headers=headers,
        json={"reviewer_user_id": "reviewer-1"},
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/workspaces/{workspace_id}/review-items/{review_item_id}/approve",
        headers=headers,
        json={"reviewer_user_id": "reviewer-1"},
    )

    assert second.status_code == 409
