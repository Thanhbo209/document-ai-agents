from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, Workspace, WorkspaceMember
from app.models.enums import WorkspaceRole


class WorkspaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, email: str, display_name: str | None = None) -> User:
        user = User(email=email, display_name=display_name)
        self.db.add(user)
        self.db.flush()
        return user

    def create_workspace(self, name: str, owner_user_id: str) -> Workspace:
        workspace = Workspace(name=name, owner_user_id=owner_user_id)
        self.db.add(workspace)
        self.db.flush()

        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_user_id,
            role=WorkspaceRole.OWNER.value,
        )
        self.db.add(membership)
        self.db.flush()

        return workspace

    def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole = WorkspaceRole.MEMBER,
    ) -> WorkspaceMember:
        membership = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role.value,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_workspace_for_user(self, workspace_id: str, user_id: str) -> Workspace | None:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )

        return self.db.scalar(statement)

    def list_workspaces_for_user(self, user_id: str) -> list[Workspace]:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
        )

        return list(self.db.scalars(statement).all())