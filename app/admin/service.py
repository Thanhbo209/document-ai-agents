from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from app.admin.schemas import (
    AdminAuditEventResponse,
    AdminDocumentMetadata,
    AdminIngestionJobSummary,
    AdminWorkspaceSummary,
)
from app.db.models import (
    AuditEvent,
    Document,
    DocumentChunk,
    DocumentFile,
    IngestionJob,
    User,
    Workspace,
    WorkspaceSubscription,
)
from app.models.enums import JobStatus


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_workspaces(self) -> list[AdminWorkspaceSummary]:
        document_counts = (
            select(
                Document.workspace_id,
                func.count(Document.id).label("document_count"),
            )
            .group_by(Document.workspace_id)
            .subquery()
        )
        failed_job_counts = (
            select(
                IngestionJob.workspace_id,
                func.count(IngestionJob.id).label("failed_job_count"),
            )
            .where(IngestionJob.status == JobStatus.FAILED.value)
            .group_by(IngestionJob.workspace_id)
            .subquery()
        )
        storage_totals = (
            select(
                DocumentFile.workspace_id,
                func.coalesce(func.sum(DocumentFile.size_bytes), 0).label("storage_bytes"),
            )
            .group_by(DocumentFile.workspace_id)
            .subquery()
        )

        statement = (
            select(
                Workspace.id,
                Workspace.name,
                Workspace.owner_user_id,
                User.email.label("owner_email"),
                func.coalesce(document_counts.c.document_count, 0).label("document_count"),
                func.coalesce(failed_job_counts.c.failed_job_count, 0).label("failed_job_count"),
                func.coalesce(storage_totals.c.storage_bytes, 0).label("storage_bytes"),
                func.coalesce(WorkspaceSubscription.plan_name, literal("free")).label("plan_name"),
                Workspace.created_at,
            )
            .join(User, User.id == Workspace.owner_user_id)
            .outerjoin(
                document_counts,
                document_counts.c.workspace_id == Workspace.id,
            )
            .outerjoin(
                failed_job_counts,
                failed_job_counts.c.workspace_id == Workspace.id,
            )
            .outerjoin(
                storage_totals,
                storage_totals.c.workspace_id == Workspace.id,
            )
            .outerjoin(
                WorkspaceSubscription,
                WorkspaceSubscription.workspace_id == Workspace.id,
            )
            .order_by(Workspace.created_at.desc())
        )

        return [
            AdminWorkspaceSummary(
                id=row.id,
                name=row.name,
                owner_user_id=row.owner_user_id,
                owner_email=row.owner_email,
                document_count=int(row.document_count),
                failed_job_count=int(row.failed_job_count),
                storage_bytes=int(row.storage_bytes),
                plan_name=row.plan_name,
                created_at=row.created_at,
            )
            for row in self.db.execute(statement)
        ]

    def list_jobs(
        self,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[AdminIngestionJobSummary]:
        statement = select(IngestionJob)

        if workspace_id is not None:
            statement = statement.where(IngestionJob.workspace_id == workspace_id)

        if status is not None:
            statement = statement.where(IngestionJob.status == status)

        statement = statement.order_by(IngestionJob.updated_at.desc())

        return [
            AdminIngestionJobSummary(
                id=job.id,
                workspace_id=job.workspace_id,
                document_id=job.document_id,
                status=job.status,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in self.db.scalars(statement).all()
        ]

    def list_document_metadata(self, workspace_id: str) -> list[AdminDocumentMetadata]:
        file_counts = (
            select(
                DocumentFile.document_id,
                func.count(DocumentFile.id).label("file_count"),
            )
            .where(DocumentFile.workspace_id == workspace_id)
            .group_by(DocumentFile.document_id)
            .subquery()
        )
        chunk_counts = (
            select(
                DocumentChunk.document_id,
                func.count(DocumentChunk.id).label("chunk_count"),
            )
            .where(DocumentChunk.workspace_id == workspace_id)
            .group_by(DocumentChunk.document_id)
            .subquery()
        )

        statement = (
            select(
                Document.id,
                Document.workspace_id,
                Document.title,
                Document.source_type,
                Document.status,
                Document.created_at,
                Document.updated_at,
                func.coalesce(file_counts.c.file_count, 0).label("file_count"),
                func.coalesce(chunk_counts.c.chunk_count, 0).label("chunk_count"),
            )
            .where(Document.workspace_id == workspace_id)
            .outerjoin(file_counts, file_counts.c.document_id == Document.id)
            .outerjoin(chunk_counts, chunk_counts.c.document_id == Document.id)
            .order_by(Document.created_at.desc())
        )

        return [
            AdminDocumentMetadata(
                id=row.id,
                workspace_id=row.workspace_id,
                title=row.title,
                source_type=row.source_type,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                file_count=int(row.file_count),
                chunk_count=int(row.chunk_count),
            )
            for row in self.db.execute(statement)
        ]

    def search_audit_events(
        self,
        workspace_id: str | None = None,
        event_type: str | None = None,
        actor_user_id: str | None = None,
    ) -> list[AdminAuditEventResponse]:
        statement = select(AuditEvent)

        if workspace_id is not None:
            statement = statement.where(AuditEvent.workspace_id == workspace_id)

        if event_type is not None:
            statement = statement.where(AuditEvent.event_type == event_type)

        if actor_user_id is not None:
            statement = statement.where(AuditEvent.actor_user_id == actor_user_id)

        statement = statement.order_by(AuditEvent.created_at.desc())

        return [
            AdminAuditEventResponse(
                id=event.id,
                workspace_id=event.workspace_id,
                actor_user_id=event.actor_user_id,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                payload=event.payload,
                created_at=event.created_at,
            )
            for event in self.db.scalars(statement).all()
        ]
