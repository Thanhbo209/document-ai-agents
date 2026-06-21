from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import User, Workspace, WorkspaceMember
from app.db.session import get_db
from app.permissions.policies import WorkspacePermission, has_workspace_permission
from app.repositories.workspaces import WorkspaceRepository


@dataclass(frozen=True)
class WorkspaceAccess:
    workspace: Workspace
    user: User
    membership: WorkspaceMember


def require_workspace_permission(
    permission: WorkspacePermission,
) -> Callable:
    def dependency(
        workspace_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> WorkspaceAccess:
        workspace = db.get(Workspace, workspace_id)

        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )

        repo = WorkspaceRepository(db)
        membership = repo.get_membership(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace.",
            )

        if not has_workspace_permission(membership.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return WorkspaceAccess(
            workspace=workspace,
            user=current_user,
            membership=membership,
        )

    return dependency
