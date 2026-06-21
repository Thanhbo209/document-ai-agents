from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.db.models import AuditEvent
from app.models.enums import WorkspaceRole
from app.repositories.workspaces import WorkspaceRepository
from tests.helpers import auth_headers_for_user, create_authenticated_workspace


def test_registered_workspace_gets_free_plan(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "billing-register@example.com",
            "password": "password123",
            "display_name": "Billing User",
            "workspace_name": "Billing Workspace",
        },
    )

    assert register.status_code == 201

    payload = register.json()
    workspace_id = payload["default_workspace_id"]
    headers = {"Authorization": f"Bearer {payload['access_token']}"}

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/billing",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["subscription"]["plan_name"] == "free"
    assert response.json()["plan"]["display_name"] == "Free"


def test_billing_summary_requires_auth(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, _ = create_authenticated_workspace(db_session)

    response = client.get(f"/api/v1/workspaces/{workspace_id}/billing")

    assert response.status_code == 401


def test_owner_can_view_billing(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/billing",
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["workspace_id"] == workspace_id
    assert payload["subscription"]["status"] == "active"
    assert payload["plan"]["limits"]["documents_limit"] == 100


def test_owner_can_list_billing_plans(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/billing/plans",
        headers=headers,
    )

    assert response.status_code == 200

    plans = {plan["name"]: plan for plan in response.json()}
    assert set(plans) == {"free", "pro"}
    assert plans["pro"]["limits"]["documents_limit"] > plans["free"]["limits"]["documents_limit"]


def test_owner_can_change_plan_from_free_to_pro(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/billing/plan",
        headers=headers,
        json={"plan_name": "pro"},
    )

    assert response.status_code == 200
    assert response.json()["subscription"]["plan_name"] == "pro"
    assert response.json()["plan"]["display_name"] == "Pro"


def test_unknown_plan_returns_400(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/billing/plan",
        headers=headers,
        json={"plan_name": "enterprise"},
    )

    assert response.status_code == 400
    assert "Unknown billing plan" in response.json()["detail"]


def test_member_cannot_change_plan(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)
    owner = repo.create_user(
        email="billing-owner@example.com",
        password_hash=hash_password("password123"),
    )
    member = repo.create_user(
        email="billing-member@example.com",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Billing Workspace",
        owner_user_id=owner.id,
    )
    repo.add_member(
        workspace_id=workspace.id,
        user_id=member.id,
        role=WorkspaceRole.MEMBER,
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/workspaces/{workspace.id}/billing/plan",
        headers=auth_headers_for_user(member.id, member.email),
        json={"plan_name": "pro"},
    )

    assert response.status_code == 403


def test_plan_change_records_audit_event(
    client: TestClient,
    db_session: Session,
) -> None:
    workspace_id, headers = create_authenticated_workspace(db_session)

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/billing/plan",
        headers=headers,
        json={"plan_name": "pro"},
    )

    assert response.status_code == 200

    events = list(
        db_session.scalars(select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)).all()
    )

    assert [event.event_type for event in events] == ["billing.plan_changed"]
    assert events[0].payload == {
        "previous_plan_name": "free",
        "plan_name": "pro",
    }
