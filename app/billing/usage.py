from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentFile, UsageEvent


class UsageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_usage(
        self,
        workspace_id: str,
        metric_name: str,
        quantity: int,
        unit: str,
        source_type: str,
        source_id: str | None = None,
        actor_user_id: str | None = None,
        usage_metadata: dict | None = None,
    ) -> UsageEvent:
        event = UsageEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            metric_name=metric_name,
            quantity=quantity,
            unit=unit,
            source_type=source_type,
            source_id=source_id,
            usage_metadata=usage_metadata or {},
        )
        self.db.add(event)
        self.db.flush()
        return event

    def sum_usage(
        self,
        workspace_id: str,
        metric_name: str,
        since: datetime | None = None,
    ) -> int:
        statement = select(func.coalesce(func.sum(UsageEvent.quantity), 0)).where(
            UsageEvent.workspace_id == workspace_id,
            UsageEvent.metric_name == metric_name,
        )

        if since is not None:
            statement = statement.where(UsageEvent.created_at >= since)

        return int(self.db.scalar(statement) or 0)

    def current_storage_bytes(self, workspace_id: str) -> int:
        statement = (
            select(func.coalesce(func.sum(DocumentFile.size_bytes), 0))
            .join(Document, Document.id == DocumentFile.document_id)
            .where(
                Document.workspace_id == workspace_id,
                Document.status != "failed",
            )
        )

        return int(self.db.scalar(statement) or 0)

    def current_document_count(self, workspace_id: str) -> int:
        statement = select(func.count(Document.id)).where(
            Document.workspace_id == workspace_id,
            Document.status != "failed",
        )

        return int(self.db.scalar(statement) or 0)

    def daily_query_count(self, workspace_id: str) -> int:
        return self.sum_usage(
            workspace_id=workspace_id,
            metric_name="query.count",
            since=datetime.now(UTC) - timedelta(days=1),
        )

    def monthly_embedding_tokens(self, workspace_id: str) -> int:
        return self.sum_usage(
            workspace_id=workspace_id,
            metric_name="embedding.tokens",
            since=datetime.now(UTC) - timedelta(days=30),
        )

    def monthly_llm_tokens(self, workspace_id: str) -> int:
        return self.sum_usage(
            workspace_id=workspace_id,
            metric_name="llm.tokens",
            since=datetime.now(UTC) - timedelta(days=30),
        )
