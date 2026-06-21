from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.admin.dependencies import require_platform_admin
from app.admin.schemas import (
    AdminAuditEventResponse,
    AdminDocumentMetadata,
    AdminIngestionJobSummary,
    AdminWorkspaceSummary,
)
from app.admin.service import AdminService
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/workspaces", response_model=list[AdminWorkspaceSummary])
def list_admin_workspaces(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_platform_admin),
) -> list[AdminWorkspaceSummary]:
    del admin_user

    return AdminService(db).list_workspaces()


@router.get("/jobs", response_model=list[AdminIngestionJobSummary])
def list_admin_jobs(
    workspace_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_platform_admin),
) -> list[AdminIngestionJobSummary]:
    del admin_user

    return AdminService(db).list_jobs(
        workspace_id=workspace_id,
        status=status_filter,
    )


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=list[AdminDocumentMetadata],
)
def list_admin_workspace_documents(
    workspace_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_platform_admin),
) -> list[AdminDocumentMetadata]:
    del admin_user

    return AdminService(db).list_document_metadata(workspace_id)


@router.get("/audit-events", response_model=list[AdminAuditEventResponse])
def search_admin_audit_events(
    workspace_id: str | None = None,
    event_type: str | None = None,
    actor_user_id: str | None = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_platform_admin),
) -> list[AdminAuditEventResponse]:
    del admin_user

    return AdminService(db).search_audit_events(
        workspace_id=workspace_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
    )


@router.get("/audit-events/export")
def export_admin_audit_events(
    export_format: Literal["csv", "json"] = Query(default="csv", alias="format"),
    workspace_id: str | None = None,
    event_type: str | None = None,
    actor_user_id: str | None = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_platform_admin),
) -> Response:
    del admin_user

    events = AdminService(db).search_audit_events(
        workspace_id=workspace_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
    )

    if export_format == "json":
        return Response(
            content=json.dumps(
                [event.model_dump(mode="json") for event in events],
                indent=2,
            ),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit-events.json"},
        )

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "workspace_id",
            "actor_user_id",
            "event_type",
            "entity_type",
            "entity_id",
            "created_at",
            "payload",
        ],
    )
    writer.writeheader()

    for event in events:
        writer.writerow(
            {
                "id": event.id,
                "workspace_id": event.workspace_id,
                "actor_user_id": event.actor_user_id,
                "event_type": event.event_type,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "created_at": event.created_at.isoformat(),
                "payload": json.dumps(event.payload, sort_keys=True),
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-events.csv"},
    )
