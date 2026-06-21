from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.db.models import Workspace
from app.db.session import get_db
from app.exports.review_exports import export_review_items_csv, export_review_items_json
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission
from app.reviews.repository import ReviewRepository

router = APIRouter(tags=["exports"])

export_reviews_access = require_workspace_permission(WorkspacePermission.EXPORT_REVIEWS)


@router.get("/workspaces/{workspace_id}/exports/review-items")
def export_review_items(
    workspace_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(export_reviews_access),
) -> Response:
    if db.get(Workspace, workspace_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    repo = ReviewRepository(db)
    items = repo.list_review_items(
        workspace_id=workspace_id,
        status=status_filter,
    )

    audit_repo = AuditEventRepository(db)
    audit_repo.record_event(
        workspace_id=workspace_id,
        event_type="export.review_items",
        entity_type="export",
        entity_id=None,
        actor_user_id=access.user.id,
        payload={
            "format": format,
            "status": status_filter,
            "item_count": len(items),
        },
    )
    db.commit()

    if format == "csv":
        return Response(
            content=export_review_items_csv(items),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=review-items.csv",
            },
        )

    return Response(
        content=export_review_items_json(items),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=review-items.json",
        },
    )
