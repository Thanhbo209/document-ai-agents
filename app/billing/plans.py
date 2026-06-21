from dataclasses import dataclass
from enum import StrEnum

from app.limits.policies import WorkspaceLimitPolicy


class PlanName(StrEnum):
    FREE = "free"
    PRO = "pro"


@dataclass(frozen=True)
class PlanDefinition:
    name: PlanName
    display_name: str
    description: str
    limits: WorkspaceLimitPolicy


FREE_PLAN = PlanDefinition(
    name=PlanName.FREE,
    display_name="Free",
    description="For local pilots and small workspaces.",
    limits=WorkspaceLimitPolicy(
        storage_bytes_limit=100 * 1024 * 1024,
        documents_limit=100,
        daily_query_limit=100,
        monthly_embedding_token_limit=500_000,
        monthly_llm_token_limit=500_000,
        concurrent_job_limit=2,
    ),
)

PRO_PLAN = PlanDefinition(
    name=PlanName.PRO,
    display_name="Pro",
    description="For larger internal teams and heavier usage.",
    limits=WorkspaceLimitPolicy(
        storage_bytes_limit=5 * 1024 * 1024 * 1024,
        documents_limit=5_000,
        daily_query_limit=5_000,
        monthly_embedding_token_limit=10_000_000,
        monthly_llm_token_limit=10_000_000,
        concurrent_job_limit=10,
    ),
)

_PLAN_CATALOG: dict[PlanName, PlanDefinition] = {
    FREE_PLAN.name: FREE_PLAN,
    PRO_PLAN.name: PRO_PLAN,
}


def get_plan_definition(plan_name: str) -> PlanDefinition:
    try:
        return _PLAN_CATALOG[PlanName(plan_name)]
    except ValueError as exc:
        raise ValueError(f"Unknown billing plan: {plan_name}") from exc


def list_plan_definitions() -> list[PlanDefinition]:
    return list(_PLAN_CATALOG.values())
