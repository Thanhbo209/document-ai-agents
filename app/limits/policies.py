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
