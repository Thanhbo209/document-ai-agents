from dataclasses import dataclass


class LimitExceededError(ValueError):
    def __init__(
        self,
        metric_name: str,
        limit: int,
        current: int,
        attempted: int,
    ) -> None:
        self.metric_name = metric_name
        self.limit = limit
        self.current = current
        self.attempted = attempted

        super().__init__(
            f"Limit exceeded for {metric_name}: "
            f"current={current}, attempted={attempted}, limit={limit}."
        )


@dataclass(frozen=True)
class WorkspaceLimitPolicy:
    storage_bytes_limit: int
    documents_limit: int
    daily_query_limit: int
    monthly_embedding_token_limit: int
    monthly_llm_token_limit: int
    concurrent_job_limit: int


FREE_WORKSPACE_POLICY = WorkspaceLimitPolicy(
    storage_bytes_limit=100 * 1024 * 1024,
    documents_limit=100,
    daily_query_limit=100,
    monthly_embedding_token_limit=500_000,
    monthly_llm_token_limit=500_000,
    concurrent_job_limit=2,
)


def get_workspace_limit_policy() -> WorkspaceLimitPolicy:
    return FREE_WORKSPACE_POLICY


def assert_within_limit(
    metric_name: str,
    current: int,
    attempted: int,
    limit: int,
) -> None:
    if current + attempted > limit:
        raise LimitExceededError(
            metric_name=metric_name,
            current=current,
            attempted=attempted,
            limit=limit,
        )
