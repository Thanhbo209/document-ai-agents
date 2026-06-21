import pytest
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password
from app.repositories.workspaces import WorkspaceRepository


@pytest.fixture
def auth_headers(db_session: Session) -> dict[str, str]:
    repo = WorkspaceRepository(db_session)
    user = repo.create_user(
        email="auth-user@example.com",
        display_name="Auth User",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Auth Workspace",
        owner_user_id=user.id,
    )
    db_session.commit()

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Test-Workspace-Id": workspace.id,
    }
