from app.models.enums import WorkspaceRole
from app.permissions.policies import WorkspacePermission, has_workspace_permission


def test_owner_has_all_workspace_permissions() -> None:
    for permission in WorkspacePermission:
        assert has_workspace_permission(WorkspaceRole.OWNER.value, permission)


def test_member_has_limited_workspace_permissions() -> None:
    assert has_workspace_permission(
        WorkspaceRole.MEMBER.value,
        WorkspacePermission.READ_DOCUMENTS,
    )
    assert has_workspace_permission(
        WorkspaceRole.MEMBER.value,
        WorkspacePermission.QUERY_DOCUMENTS,
    )
    assert not has_workspace_permission(
        WorkspaceRole.MEMBER.value,
        WorkspacePermission.DECIDE_REVIEWS,
    )
    assert not has_workspace_permission(
        WorkspaceRole.MEMBER.value,
        WorkspacePermission.EXPORT_REVIEWS,
    )
