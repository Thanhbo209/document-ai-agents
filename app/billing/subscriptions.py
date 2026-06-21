from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.billing.plans import (
    PlanDefinition,
    PlanName,
    get_plan_definition,
    list_plan_definitions,
)
from app.db.models import WorkspaceSubscription


class WorkspaceSubscriptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_repo = AuditEventRepository(db)

    def get_subscription(self, workspace_id: str) -> WorkspaceSubscription | None:
        statement = select(WorkspaceSubscription).where(
            WorkspaceSubscription.workspace_id == workspace_id
        )

        return self.db.scalar(statement)

    def get_or_create_subscription(
        self,
        workspace_id: str,
        plan_name: str = PlanName.FREE.value,
        actor_user_id: str | None = None,
    ) -> WorkspaceSubscription:
        subscription = self.get_subscription(workspace_id)

        if subscription is not None:
            return subscription

        get_plan_definition(plan_name)

        subscription = WorkspaceSubscription(
            workspace_id=workspace_id,
            plan_name=plan_name,
            status="active",
        )
        self.db.add(subscription)
        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="billing.subscription.created",
            entity_type="workspace_subscription",
            entity_id=subscription.id,
            payload={
                "plan_name": plan_name,
                "status": subscription.status,
            },
        )

        return subscription

    def set_plan(
        self,
        workspace_id: str,
        plan_name: str,
        actor_user_id: str | None = None,
    ) -> WorkspaceSubscription:
        get_plan_definition(plan_name)

        subscription = self.get_or_create_subscription(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
        )
        previous_plan_name = subscription.plan_name

        if previous_plan_name == plan_name:
            return subscription

        subscription.plan_name = plan_name
        subscription.status = "active"
        self.db.flush()

        self.audit_repo.record_event(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type="billing.plan_changed",
            entity_type="workspace_subscription",
            entity_id=subscription.id,
            payload={
                "previous_plan_name": previous_plan_name,
                "plan_name": plan_name,
            },
        )

        return subscription

    def list_available_plans(self) -> list[PlanDefinition]:
        return list_plan_definitions()
