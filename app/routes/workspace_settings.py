from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.billing.plans import get_plan_definition
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.db.session import get_db
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission

router = APIRouter(tags=["workspace-settings"])

manage_workspace_settings_access = require_workspace_permission(
    WorkspacePermission.MANAGE_WORKSPACE,
    block_inactive_workspace=False,
)


class WorkspaceSettingsPlanResponse(BaseModel):
    name: str
    display_name: str
    status: str


class WorkspaceSettingsResponse(BaseModel):
    workspace_id: str
    name: str
    status: str
    deletion_requested_at: datetime | None
    deleted_at: datetime | None
    plan: WorkspaceSettingsPlanResponse | None
    retention_notes: list[str]


@router.get(
    "/workspaces/{workspace_id}/settings",
    response_model=WorkspaceSettingsResponse,
)
def get_workspace_settings(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_settings_access),
) -> WorkspaceSettingsResponse:
    subscription = WorkspaceSubscriptionRepository(db).get_or_create_subscription(workspace_id)
    plan = get_plan_definition(subscription.plan_name)
    db.commit()

    return WorkspaceSettingsResponse(
        workspace_id=workspace_id,
        name=access.workspace.name,
        status=access.workspace.status,
        deletion_requested_at=access.workspace.deletion_requested_at,
        deleted_at=access.workspace.deleted_at,
        plan=WorkspaceSettingsPlanResponse(
            name=plan.name.value,
            display_name=plan.display_name,
            status=subscription.status,
        ),
        retention_notes=[
            "Workspace deletion is a soft-delete lifecycle transition in this phase.",
            "Soft-deleted data may remain in rows and backups until permanent deletion exists.",
            "Owner exports include workspace-owned content.",
            "Admin support views remain metadata-only.",
        ],
    )
