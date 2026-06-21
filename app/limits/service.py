from app.billing.plans import get_plan_definition
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.billing.usage import UsageRepository
from app.limits.policies import (
    LimitExceededError,
    WorkspaceLimitPolicy,
    assert_within_limit,
)


class QuotaService:
    def __init__(
        self,
        usage_repo: UsageRepository,
        subscription_repo: WorkspaceSubscriptionRepository,
    ) -> None:
        self.usage_repo = usage_repo
        self.subscription_repo = subscription_repo

    def _policy_for_workspace(self, workspace_id: str) -> WorkspaceLimitPolicy:
        subscription = self.subscription_repo.get_or_create_subscription(workspace_id)
        return get_plan_definition(subscription.plan_name).limits

    def assert_can_upload(
        self,
        workspace_id: str,
        file_size_bytes: int,
    ) -> None:
        policy = self._policy_for_workspace(workspace_id)

        assert_within_limit(
            metric_name="storage.bytes",
            current=self.usage_repo.current_storage_bytes(workspace_id),
            attempted=file_size_bytes,
            limit=policy.storage_bytes_limit,
        )

        assert_within_limit(
            metric_name="documents.count",
            current=self.usage_repo.current_document_count(workspace_id),
            attempted=1,
            limit=policy.documents_limit,
        )

    def assert_can_query(
        self,
        workspace_id: str,
    ) -> None:
        policy = self._policy_for_workspace(workspace_id)

        assert_within_limit(
            metric_name="query.count",
            current=self.usage_repo.daily_query_count(workspace_id),
            attempted=1,
            limit=policy.daily_query_limit,
        )

    def assert_can_embed_tokens(
        self,
        workspace_id: str,
        token_count: int,
    ) -> None:
        policy = self._policy_for_workspace(workspace_id)

        assert_within_limit(
            metric_name="embedding.tokens",
            current=self.usage_repo.monthly_embedding_tokens(workspace_id),
            attempted=token_count,
            limit=policy.monthly_embedding_token_limit,
        )

    def assert_can_use_llm_tokens(
        self,
        workspace_id: str,
        token_count: int,
    ) -> None:
        policy = self._policy_for_workspace(workspace_id)

        assert_within_limit(
            metric_name="llm.tokens",
            current=self.usage_repo.monthly_llm_tokens(workspace_id),
            attempted=token_count,
            limit=policy.monthly_llm_token_limit,
        )


def quota_error_response(exc: LimitExceededError) -> dict:
    return {
        "message": "Workspace limit exceeded.",
        "metric_name": exc.metric_name,
        "limit": exc.limit,
        "current": exc.current,
        "attempted": exc.attempted,
    }
