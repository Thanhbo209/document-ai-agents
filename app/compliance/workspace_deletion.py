from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.db.models import Workspace, utc_now
from app.models.enums import WorkspaceStatus


class WorkspaceDeletionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_repo = AuditEventRepository(db)

    def request_deletion(
        self,
        workspace_id: str,
        actor_user_id: str,
        reason: str | None = None,
    ) -> Workspace:
        workspace = self._workspace_or_error(workspace_id)

        if workspace.status != WorkspaceStatus.ACTIVE.value:
            raise ValueError("Only active workspaces can be marked for deletion.")

        workspace.status = WorkspaceStatus.PENDING_DELETION.value
        workspace.deletion_requested_at = utc_now()
        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="compliance.workspace_deletion_requested",
            entity_type="workspace",
            entity_id=workspace_id,
            payload={"reason": reason},
        )

        return workspace

    def mark_deleted(
        self,
        workspace_id: str,
        actor_user_id: str,
    ) -> Workspace:
        workspace = self._workspace_or_error(workspace_id)

        if workspace.status == WorkspaceStatus.DELETED.value:
            return workspace

        workspace.status = WorkspaceStatus.DELETED.value
        workspace.deleted_at = utc_now()

        if workspace.deletion_requested_at is None:
            workspace.deletion_requested_at = workspace.deleted_at

        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="compliance.workspace_deleted",
            entity_type="workspace",
            entity_id=workspace_id,
            payload={},
        )

        return workspace

    def _workspace_or_error(self, workspace_id: str) -> Workspace:
        workspace = self.db.get(Workspace, workspace_id)

        if workspace is None:
            raise ValueError("Workspace not found.")

        return workspace
