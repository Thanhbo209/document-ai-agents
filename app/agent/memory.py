from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AgentPlanStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class PlannedToolCall:
    step_id: str
    tool_name: str
    payload: dict[str, Any]
    requires_human_review: bool = False


@dataclass
class AgentStepLog:
    step_id: str
    tool_name: str
    status: str
    user_message: str
    error: str | None = None
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlanLog:
    plan_id: str
    workspace_id: str
    user_request: str
    status: AgentPlanStatus
    planned_steps: list[PlannedToolCall]
    step_logs: list[AgentStepLog] = field(default_factory=list)


class InMemoryAgentMemory:
    def __init__(self) -> None:
        self._plans: dict[str, AgentPlanLog] = {}

    def create_plan(
        self,
        workspace_id: str,
        user_request: str,
        planned_steps: list[PlannedToolCall],
    ) -> AgentPlanLog:
        plan = AgentPlanLog(
            plan_id=str(uuid4()),
            workspace_id=workspace_id,
            user_request=user_request,
            status=AgentPlanStatus.RUNNING,
            planned_steps=planned_steps,
        )

        self._plans[plan.plan_id] = plan

        return plan

    def record_step(
        self,
        plan_id: str,
        step_log: AgentStepLog,
    ) -> None:
        plan = self.get_plan(plan_id)
        plan.step_logs.append(step_log)

    def update_status(
        self,
        plan_id: str,
        status: AgentPlanStatus,
    ) -> None:
        plan = self.get_plan(plan_id)
        plan.status = status

    def get_plan(self, plan_id: str) -> AgentPlanLog:
        plan = self._plans.get(plan_id)

        if plan is None:
            raise KeyError(f"Plan not found: {plan_id}")

        return plan

    def list_plans_for_workspace(self, workspace_id: str) -> list[AgentPlanLog]:
        return [plan for plan in self._plans.values() if plan.workspace_id == workspace_id]
