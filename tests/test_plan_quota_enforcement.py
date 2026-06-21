import pytest
from sqlalchemy.orm import Session

from app.billing.plans import get_plan_definition
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.billing.usage import UsageRepository
from app.limits.policies import LimitExceededError
from app.limits.service import QuotaService
from tests.helpers import create_authenticated_workspace


def test_free_plan_limits_are_used_by_quota_service(db_session: Session) -> None:
    workspace_id, _ = create_authenticated_workspace(db_session)
    usage_repo = UsageRepository(db_session)

    for _ in range(100):
        usage_repo.record_usage(
            workspace_id=workspace_id,
            metric_name="query.count",
            quantity=1,
            unit="query",
            source_type="conversation",
        )

    db_session.commit()

    quota_service = QuotaService(
        usage_repo=usage_repo,
        subscription_repo=WorkspaceSubscriptionRepository(db_session),
    )

    with pytest.raises(LimitExceededError) as exc_info:
        quota_service.assert_can_query(workspace_id)

    assert exc_info.value.metric_name == "query.count"
    assert exc_info.value.limit == 100


def test_pro_plan_limits_are_higher_than_free() -> None:
    free_plan = get_plan_definition("free")
    pro_plan = get_plan_definition("pro")

    assert pro_plan.limits.storage_bytes_limit > free_plan.limits.storage_bytes_limit
    assert pro_plan.limits.documents_limit > free_plan.limits.documents_limit
    assert pro_plan.limits.daily_query_limit > free_plan.limits.daily_query_limit
    assert (
        pro_plan.limits.monthly_embedding_token_limit
        > free_plan.limits.monthly_embedding_token_limit
    )
    assert pro_plan.limits.monthly_llm_token_limit > free_plan.limits.monthly_llm_token_limit
    assert pro_plan.limits.concurrent_job_limit > free_plan.limits.concurrent_job_limit


def test_pro_plan_allows_usage_above_free_limit(db_session: Session) -> None:
    workspace_id, _ = create_authenticated_workspace(db_session)
    usage_repo = UsageRepository(db_session)
    subscription_repo = WorkspaceSubscriptionRepository(db_session)
    subscription_repo.set_plan(workspace_id=workspace_id, plan_name="pro")

    for _ in range(100):
        usage_repo.record_usage(
            workspace_id=workspace_id,
            metric_name="query.count",
            quantity=1,
            unit="query",
            source_type="conversation",
        )

    db_session.commit()

    quota_service = QuotaService(
        usage_repo=usage_repo,
        subscription_repo=subscription_repo,
    )

    quota_service.assert_can_query(workspace_id)
