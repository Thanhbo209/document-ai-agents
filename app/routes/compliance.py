from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.compliance.workspace_deletion import WorkspaceDeletionService
from app.compliance.workspace_export import WorkspaceExportService
from app.db.models import Workspace
from app.db.session import get_db
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission

router = APIRouter(tags=["compliance"])

manage_workspace_lifecycle_access = require_workspace_permission(
    WorkspacePermission.MANAGE_WORKSPACE,
    block_inactive_workspace=False,
)


class WorkspaceStatusResponse(BaseModel):
    workspace_id: str
    status: str
    deletion_requested_at: datetime | None
    deleted_at: datetime | None


class DeleteRequestBody(BaseModel):
    reason: str | None = None


@router.get("/workspaces/{workspace_id}/compliance/export")
def export_workspace_data(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_lifecycle_access),
) -> dict[str, Any]:
    try:
        payload = WorkspaceExportService(db).export_workspace_data(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    db.commit()
    return payload


@router.post(
    "/workspaces/{workspace_id}/compliance/delete-request",
    response_model=WorkspaceStatusResponse,
)
def request_workspace_deletion(
    workspace_id: str,
    request: DeleteRequestBody,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_lifecycle_access),
) -> WorkspaceStatusResponse:
    try:
        workspace = WorkspaceDeletionService(db).request_deletion(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    db.commit()
    return _workspace_status_response(workspace)


@router.post(
    "/workspaces/{workspace_id}/compliance/mark-deleted",
    response_model=WorkspaceStatusResponse,
)
def mark_workspace_deleted(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_lifecycle_access),
) -> WorkspaceStatusResponse:
    try:
        workspace = WorkspaceDeletionService(db).mark_deleted(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    db.commit()
    return _workspace_status_response(workspace)


def _workspace_status_response(workspace: Workspace) -> WorkspaceStatusResponse:
    return WorkspaceStatusResponse(
        workspace_id=workspace.id,
        status=workspace.status,
        deletion_requested_at=workspace.deletion_requested_at,
        deleted_at=workspace.deleted_at,
    )
