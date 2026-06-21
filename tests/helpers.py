from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password
from app.models.enums import WorkspaceRole
from app.repositories.workspaces import WorkspaceRepository


def create_authenticated_workspace(
    db_session: Session,
    email: str = "auth-user@example.com",
    role: WorkspaceRole = WorkspaceRole.OWNER,
) -> tuple[str, dict[str, str]]:
    repo = WorkspaceRepository(db_session)
    user = repo.create_user(
        email=email,
        display_name="Auth User",
        password_hash=hash_password("password123"),
    )
    workspace = repo.create_workspace(
        name="Auth Workspace",
        owner_user_id=user.id,
    )

    if role == WorkspaceRole.MEMBER:
        # create_workspace already makes the user owner; tests needing member
        # should create a second user and add membership directly.
        pass

    db_session.commit()

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return workspace.id, {"Authorization": f"Bearer {token}"}


def auth_headers_for_user(user_id: str, email: str) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        email=email,
    )

    return {"Authorization": f"Bearer {token}"}
