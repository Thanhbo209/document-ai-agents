from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.db.models import (
    AuditEvent,
    Citation,
    ConversationMessage,
    Document,
    DocumentChunk,
    DocumentFile,
    ReviewItem,
    UsageEvent,
    Workspace,
    WorkspaceMember,
    WorkspaceSubscription,
)


class WorkspaceExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_repo = AuditEventRepository(db)

    def export_workspace_data(
        self,
        workspace_id: str,
        actor_user_id: str,
    ) -> dict[str, Any]:
        workspace = self.db.get(Workspace, workspace_id)

        if workspace is None:
            raise ValueError("Workspace not found.")

        event = self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="compliance.workspace_exported",
            entity_type="workspace",
            entity_id=workspace_id,
            payload={"format": "json"},
        )

        return {
            "exported_at": _serialize_datetime(event.created_at),
            "workspace": _workspace_payload(workspace),
            "members": self._members_payload(workspace_id),
            "documents": self._documents_payload(workspace_id),
            "files": self._files_payload(workspace_id),
            "chunks": self._chunks_payload(workspace_id),
            "conversations": self._conversations_payload(workspace_id),
            "citations": self._citations_payload(workspace_id),
            "review_items": self._review_items_payload(workspace_id),
            "audit_events": self._audit_events_payload(workspace_id),
            "usage_events": self._usage_events_payload(workspace_id),
            "subscription": self._subscription_payload(workspace_id),
        }

    def _members_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        members = self.db.scalars(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.created_at.asc())
        ).all()

        return [
            {
                "id": member.id,
                "workspace_id": member.workspace_id,
                "user_id": member.user_id,
                "role": member.role,
                "created_at": _serialize_datetime(member.created_at),
                "updated_at": _serialize_datetime(member.updated_at),
            }
            for member in members
        ]

    def _documents_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        documents = self.db.scalars(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.asc())
        ).all()

        return [
            {
                "id": document.id,
                "workspace_id": document.workspace_id,
                "title": document.title,
                "source_type": document.source_type,
                "status": document.status,
                "created_at": _serialize_datetime(document.created_at),
                "updated_at": _serialize_datetime(document.updated_at),
            }
            for document in documents
        ]

    def _files_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        files = self.db.scalars(
            select(DocumentFile)
            .where(DocumentFile.workspace_id == workspace_id)
            .order_by(DocumentFile.created_at.asc())
        ).all()

        return [
            {
                "id": file.id,
                "workspace_id": file.workspace_id,
                "document_id": file.document_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": file.size_bytes,
                "storage_key": file.storage_key,
                "checksum_sha256": file.checksum_sha256,
                "created_at": _serialize_datetime(file.created_at),
                "updated_at": _serialize_datetime(file.updated_at),
            }
            for file in files
        ]

    def _chunks_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        chunks = self.db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.workspace_id == workspace_id)
            .order_by(DocumentChunk.document_id.asc(), DocumentChunk.chunk_index.asc())
        ).all()

        return [
            {
                "id": chunk.id,
                "workspace_id": chunk.workspace_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "source_page": chunk.source_page,
                "source_start_offset": chunk.source_start_offset,
                "source_end_offset": chunk.source_end_offset,
                "token_count": chunk.token_count,
                "source_metadata": chunk.source_metadata,
                "created_at": _serialize_datetime(chunk.created_at),
                "updated_at": _serialize_datetime(chunk.updated_at),
            }
            for chunk in chunks
        ]

    def _conversations_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        messages = self.db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.workspace_id == workspace_id)
            .order_by(ConversationMessage.created_at.asc())
        ).all()

        return [
            {
                "id": message.id,
                "workspace_id": message.workspace_id,
                "user_id": message.user_id,
                "role": message.role,
                "content": message.content,
                "created_at": _serialize_datetime(message.created_at),
                "updated_at": _serialize_datetime(message.updated_at),
            }
            for message in messages
        ]

    def _citations_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        citations = self.db.scalars(
            select(Citation)
            .join(ConversationMessage, ConversationMessage.id == Citation.message_id)
            .where(ConversationMessage.workspace_id == workspace_id)
            .order_by(Citation.created_at.asc())
        ).all()

        return [
            {
                "id": citation.id,
                "message_id": citation.message_id,
                "chunk_id": citation.chunk_id,
                "rank": citation.rank,
                "relevance_score": citation.relevance_score,
                "quote": citation.quote,
                "created_at": _serialize_datetime(citation.created_at),
                "updated_at": _serialize_datetime(citation.updated_at),
            }
            for citation in citations
        ]

    def _review_items_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        review_items = self.db.scalars(
            select(ReviewItem)
            .where(ReviewItem.workspace_id == workspace_id)
            .order_by(ReviewItem.created_at.asc())
        ).all()

        return [
            {
                "id": item.id,
                "workspace_id": item.workspace_id,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "field_name": item.field_name,
                "original_value": item.original_value,
                "reviewed_value": item.reviewed_value,
                "evidence": item.evidence,
                "status": item.status,
                "reviewer_user_id": item.reviewer_user_id,
                "reviewed_at": _serialize_datetime(item.reviewed_at),
                "comments": item.comments,
                "created_at": _serialize_datetime(item.created_at),
                "updated_at": _serialize_datetime(item.updated_at),
            }
            for item in review_items
        ]

    def _audit_events_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        events = self.db.scalars(
            select(AuditEvent)
            .where(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.created_at.asc())
        ).all()

        return [
            {
                "id": event.id,
                "workspace_id": event.workspace_id,
                "actor_user_id": event.actor_user_id,
                "event_type": event.event_type,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "payload": event.payload,
                "created_at": _serialize_datetime(event.created_at),
                "updated_at": _serialize_datetime(event.updated_at),
            }
            for event in events
        ]

    def _usage_events_payload(self, workspace_id: str) -> list[dict[str, Any]]:
        events = self.db.scalars(
            select(UsageEvent)
            .where(UsageEvent.workspace_id == workspace_id)
            .order_by(UsageEvent.created_at.asc())
        ).all()

        return [
            {
                "id": event.id,
                "workspace_id": event.workspace_id,
                "actor_user_id": event.actor_user_id,
                "metric_name": event.metric_name,
                "quantity": event.quantity,
                "unit": event.unit,
                "source_type": event.source_type,
                "source_id": event.source_id,
                "usage_metadata": event.usage_metadata,
                "created_at": _serialize_datetime(event.created_at),
                "updated_at": _serialize_datetime(event.updated_at),
            }
            for event in events
        ]

    def _subscription_payload(self, workspace_id: str) -> dict[str, Any] | None:
        subscription = self.db.scalar(
            select(WorkspaceSubscription).where(WorkspaceSubscription.workspace_id == workspace_id)
        )

        if subscription is None:
            return None

        return {
            "id": subscription.id,
            "workspace_id": subscription.workspace_id,
            "plan_name": subscription.plan_name,
            "status": subscription.status,
            "current_period_start": _serialize_datetime(subscription.current_period_start),
            "current_period_end": _serialize_datetime(subscription.current_period_end),
            "created_at": _serialize_datetime(subscription.created_at),
            "updated_at": _serialize_datetime(subscription.updated_at),
        }


def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_user_id": workspace.owner_user_id,
        "status": workspace.status,
        "deletion_requested_at": _serialize_datetime(workspace.deletion_requested_at),
        "deleted_at": _serialize_datetime(workspace.deleted_at),
        "created_at": _serialize_datetime(workspace.created_at),
        "updated_at": _serialize_datetime(workspace.updated_at),
    }


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
