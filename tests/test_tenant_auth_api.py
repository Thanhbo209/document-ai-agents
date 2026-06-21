from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password
from app.models.enums import WorkspaceRole
from app.repositories.workspaces import WorkspaceRepository


def create_user_with_workspace(
    db_session: Session,
    email: str,
) -> tuple[str, str, dict[str, str]]:
    repo = WorkspaceRepository(db_session)
    user = repo.create_user(
        email=email,
        display_name=email,
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name=f"{email} workspace",
        owner_user_id=user.id,
    )
    db_session.commit()

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return user.id, workspace.id, {"Authorization": f"Bearer {token}"}


def test_user_cannot_list_other_workspace_documents(
    client: TestClient,
    db_session: Session,
) -> None:
    _, workspace_a, headers_a = create_user_with_workspace(
        db_session,
        "a@example.com",
    )
    _, workspace_b, _ = create_user_with_workspace(
        db_session,
        "b@example.com",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace_b}/documents",
        headers=headers_a,
    )

    assert response.status_code == 403


def test_unauthenticated_workspace_request_is_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    _, workspace_id, _ = create_user_with_workspace(
        db_session,
        "owner@example.com",
    )

    response = client.get(f"/api/v1/workspaces/{workspace_id}/documents")

    assert response.status_code == 401


def test_member_cannot_export_review_items(
    client: TestClient,
    db_session: Session,
) -> None:
    repo = WorkspaceRepository(db_session)

    owner = repo.create_user(
        email="owner@example.com",
        password_hash=hash_password("password123"),
    )
    member = repo.create_user(
        email="member@example.com",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Role Workspace",
        owner_user_id=owner.id,
    )
    repo.add_member(
        workspace_id=workspace.id,
        user_id=member.id,
        role=WorkspaceRole.MEMBER,
    )
    db_session.commit()

    member_headers = {"Authorization": f"Bearer {create_access_token(member.id, member.email)}"}

    response = client.get(
        f"/api/v1/workspaces/{workspace.id}/exports/review-items",
        headers=member_headers,
    )

    assert response.status_code == 403


def test_owner_can_export_review_items(
    client: TestClient,
    db_session: Session,
) -> None:
    _, workspace_id, headers = create_user_with_workspace(
        db_session,
        "export-owner@example.com",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/exports/review-items",
        headers=headers,
    )

    assert response.status_code == 200
