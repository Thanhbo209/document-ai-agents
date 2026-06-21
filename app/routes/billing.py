from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.billing.plans import PlanDefinition, get_plan_definition
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.db.models import WorkspaceSubscription
from app.db.session import get_db
from app.limits.policies import WorkspaceLimitPolicy
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission

router = APIRouter(tags=["billing"])

manage_workspace_access = require_workspace_permission(WorkspacePermission.MANAGE_WORKSPACE)


class PlanLimitsResponse(BaseModel):
    storage_bytes_limit: int
    documents_limit: int
    daily_query_limit: int
    monthly_embedding_token_limit: int
    monthly_llm_token_limit: int
    concurrent_job_limit: int


class BillingPlanResponse(BaseModel):
    name: str
    display_name: str
    description: str
    limits: PlanLimitsResponse


class BillingSubscriptionResponse(BaseModel):
    id: str
    workspace_id: str
    plan_name: str
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None


class BillingSummaryResponse(BaseModel):
    workspace_id: str
    subscription: BillingSubscriptionResponse
    plan: BillingPlanResponse


class ChangePlanRequest(BaseModel):
    plan_name: str


@router.get(
    "/workspaces/{workspace_id}/billing",
    response_model=BillingSummaryResponse,
)
def get_workspace_billing(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_access),
) -> BillingSummaryResponse:
    del access

    subscription_repo = WorkspaceSubscriptionRepository(db)
    subscription = subscription_repo.get_or_create_subscription(workspace_id)
    plan = _plan_for_subscription(subscription)
    db.commit()

    return BillingSummaryResponse(
        workspace_id=workspace_id,
        subscription=_subscription_response(subscription),
        plan=_plan_response(plan),
    )


@router.get(
    "/workspaces/{workspace_id}/billing/plans",
    response_model=list[BillingPlanResponse],
)
def list_workspace_billing_plans(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_access),
) -> list[BillingPlanResponse]:
    del workspace_id, access

    return [
        _plan_response(plan) for plan in WorkspaceSubscriptionRepository(db).list_available_plans()
    ]


@router.post(
    "/workspaces/{workspace_id}/billing/plan",
    response_model=BillingSummaryResponse,
)
def change_workspace_plan(
    workspace_id: str,
    request: ChangePlanRequest,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_access),
) -> BillingSummaryResponse:
    subscription_repo = WorkspaceSubscriptionRepository(db)

    try:
        subscription = subscription_repo.set_plan(
            workspace_id=workspace_id,
            plan_name=request.plan_name,
            actor_user_id=access.user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    plan = _plan_for_subscription(subscription)
    db.commit()

    return BillingSummaryResponse(
        workspace_id=workspace_id,
        subscription=_subscription_response(subscription),
        plan=_plan_response(plan),
    )


def _plan_for_subscription(subscription: WorkspaceSubscription) -> PlanDefinition:
    return get_plan_definition(subscription.plan_name)


def _subscription_response(
    subscription: WorkspaceSubscription,
) -> BillingSubscriptionResponse:
    return BillingSubscriptionResponse(
        id=subscription.id,
        workspace_id=subscription.workspace_id,
        plan_name=subscription.plan_name,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
    )


def _plan_response(plan: PlanDefinition) -> BillingPlanResponse:
    return BillingPlanResponse(
        name=plan.name.value,
        display_name=plan.display_name,
        description=plan.description,
        limits=_limits_response(plan.limits),
    )


def _limits_response(limits: WorkspaceLimitPolicy) -> PlanLimitsResponse:
    return PlanLimitsResponse(
        storage_bytes_limit=limits.storage_bytes_limit,
        documents_limit=limits.documents_limit,
        daily_query_limit=limits.daily_query_limit,
        monthly_embedding_token_limit=limits.monthly_embedding_token_limit,
        monthly_llm_token_limit=limits.monthly_llm_token_limit,
        concurrent_job_limit=limits.concurrent_job_limit,
    )
