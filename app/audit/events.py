from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent


class AuditEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_event(
        self,
        workspace_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str | None = None,
        actor_user_id: str | None = None,
        payload: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list_events_for_workspace(
        self,
        workspace_id: str,
        limit: int = 100,
    ) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def list_events_for_entity(
        self,
        workspace_id: str,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(
                AuditEvent.workspace_id == workspace_id,
                AuditEvent.entity_type == entity_type,
                AuditEvent.entity_id == entity_id,
            )
            .order_by(AuditEvent.created_at.asc())
        )

        return list(self.db.scalars(statement).all())
