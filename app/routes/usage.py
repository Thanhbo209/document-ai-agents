from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.billing.plans import get_plan_definition
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.billing.usage import UsageRepository
from app.db.session import get_db
from app.limits.policies import WorkspaceLimitPolicy
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission

router = APIRouter(tags=["usage"])

manage_workspace_access = require_workspace_permission(WorkspacePermission.MANAGE_WORKSPACE)


class UsageMetricResponse(BaseModel):
    metric_name: str
    current: int
    limit: int | None
    unit: str


class UsagePlanResponse(BaseModel):
    name: str
    display_name: str
    status: str


class UsageSummaryResponse(BaseModel):
    workspace_id: str
    plan: UsagePlanResponse
    metrics: list[UsageMetricResponse]


@router.get(
    "/workspaces/{workspace_id}/usage",
    response_model=UsageSummaryResponse,
)
def get_workspace_usage(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(manage_workspace_access),
) -> UsageSummaryResponse:
    del access

    usage_repo = UsageRepository(db)
    subscription = WorkspaceSubscriptionRepository(db).get_or_create_subscription(workspace_id)
    plan = get_plan_definition(subscription.plan_name)
    db.commit()

    return UsageSummaryResponse(
        workspace_id=workspace_id,
        plan=UsagePlanResponse(
            name=plan.name.value,
            display_name=plan.display_name,
            status=subscription.status,
        ),
        metrics=_usage_metrics(
            usage_repo=usage_repo,
            workspace_id=workspace_id,
            policy=plan.limits,
        ),
    )


def _usage_metrics(
    usage_repo: UsageRepository,
    workspace_id: str,
    policy: WorkspaceLimitPolicy,
) -> list[UsageMetricResponse]:
    return [
        UsageMetricResponse(
            metric_name="storage.bytes",
            current=usage_repo.current_storage_bytes(workspace_id),
            limit=policy.storage_bytes_limit,
            unit="bytes",
        ),
        UsageMetricResponse(
            metric_name="documents.count",
            current=usage_repo.current_document_count(workspace_id),
            limit=policy.documents_limit,
            unit="document",
        ),
        UsageMetricResponse(
            metric_name="query.count.daily",
            current=usage_repo.daily_query_count(workspace_id),
            limit=policy.daily_query_limit,
            unit="query",
        ),
        UsageMetricResponse(
            metric_name="chunk.tokens.monthly",
            current=usage_repo.sum_usage(
                workspace_id=workspace_id,
                metric_name="chunk.tokens",
            ),
            limit=None,
            unit="token",
        ),
        UsageMetricResponse(
            metric_name="llm.tokens.monthly",
            current=usage_repo.monthly_llm_tokens(workspace_id),
            limit=policy.monthly_llm_token_limit,
            unit="token",
        ),
    ]
