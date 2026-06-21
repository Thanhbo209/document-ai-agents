from enum import StrEnum

from app.models.enums import WorkspaceRole


class WorkspacePermission(StrEnum):
    READ_DOCUMENTS = "read_documents"
    UPLOAD_DOCUMENTS = "upload_documents"
    QUERY_DOCUMENTS = "query_documents"
    READ_REVIEWS = "read_reviews"
    CREATE_REVIEWS = "create_reviews"
    DECIDE_REVIEWS = "decide_reviews"
    EXPORT_REVIEWS = "export_reviews"
    MANAGE_WORKSPACE = "manage_workspace"


_ROLE_PERMISSIONS: dict[WorkspaceRole, set[WorkspacePermission]] = {
    WorkspaceRole.OWNER: {
        WorkspacePermission.READ_DOCUMENTS,
        WorkspacePermission.UPLOAD_DOCUMENTS,
        WorkspacePermission.QUERY_DOCUMENTS,
        WorkspacePermission.READ_REVIEWS,
        WorkspacePermission.CREATE_REVIEWS,
        WorkspacePermission.DECIDE_REVIEWS,
        WorkspacePermission.EXPORT_REVIEWS,
        WorkspacePermission.MANAGE_WORKSPACE,
    },
    WorkspaceRole.MEMBER: {
        WorkspacePermission.READ_DOCUMENTS,
        WorkspacePermission.UPLOAD_DOCUMENTS,
        WorkspacePermission.QUERY_DOCUMENTS,
        WorkspacePermission.READ_REVIEWS,
        WorkspacePermission.CREATE_REVIEWS,
    },
}


def has_workspace_permission(
    role: str,
    permission: WorkspacePermission,
) -> bool:
    workspace_role = WorkspaceRole(role)

    return permission in _ROLE_PERMISSIONS[workspace_role]
