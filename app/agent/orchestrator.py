from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.memory import (
    AgentPlanStatus,
    AgentStepLog,
    InMemoryAgentMemory,
    PlannedToolCall,
)
from app.agent.tools.base import (
    TenantScopeError,
    ToolExecutionContext,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolRegistry,
    ToolRegistryError,
    ensure_tool_result_scoped,
)


@dataclass(frozen=True)
class AgentRunRequest:
    workspace_id: str
    user_request: str
    user_id: str | None = None
    payload: dict[str, Any] | None = None
    approved_step_ids: list[str] | None = None


@dataclass(frozen=True)
class AgentRunResult:
    plan_id: str
    status: AgentPlanStatus
    user_message: str
    outputs: list[dict[str, Any]]
    step_logs: list[AgentStepLog]


class SimpleAgentPlanner:
    def plan(
        self,
        user_request: str,
        payload: dict[str, Any] | None = None,
    ) -> list[PlannedToolCall]:
        request = user_request.lower()
        base_payload = payload or {}

        if "compare" in request:
            steps = [
                PlannedToolCall(
                    step_id="step-1",
                    tool_name="compare_documents",
                    payload=base_payload,
                    requires_human_review=False,
                )
            ]

            if "report" in request:
                steps.append(
                    PlannedToolCall(
                        step_id="step-2",
                        tool_name="generate_report",
                        payload=base_payload,
                        requires_human_review=True,
                    )
                )

            return steps

        if "extract" in request or "json" in request:
            return [
                PlannedToolCall(
                    step_id="step-1",
                    tool_name="extract_fields",
                    payload=base_payload,
                    requires_human_review=True,
                )
            ]

        if "report" in request:
            return [
                PlannedToolCall(
                    step_id="step-1",
                    tool_name="generate_report",
                    payload=base_payload,
                    requires_human_review=True,
                )
            ]

        if "summarize" in request or "summary" in request:
            return [
                PlannedToolCall(
                    step_id="step-1",
                    tool_name="summarize_document",
                    payload=base_payload,
                    requires_human_review=False,
                )
            ]

        return [
            PlannedToolCall(
                step_id="step-1",
                tool_name="search_documents",
                payload=base_payload,
                requires_human_review=False,
            )
        ]


class AgentOrchestrator:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        memory: InMemoryAgentMemory,
        planner: SimpleAgentPlanner | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.memory = memory
        self.planner = planner or SimpleAgentPlanner()

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        planned_steps = self.planner.plan(
            user_request=request.user_request,
            payload=request.payload,
        )
        approved_step_ids = set(request.approved_step_ids or [])

        plan = self.memory.create_plan(
            workspace_id=request.workspace_id,
            user_request=request.user_request,
            planned_steps=planned_steps,
        )

        outputs: list[dict[str, Any]] = []

        for step in planned_steps:
            if step.requires_human_review and step.step_id not in approved_step_ids:
                step_log = AgentStepLog(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status=ToolExecutionStatus.NEEDS_REVIEW.value,
                    user_message=(f"Step '{step.tool_name}' needs human review before execution."),
                    output={
                        "workspace_id": request.workspace_id,
                        "step_id": step.step_id,
                    },
                )
                self.memory.record_step(plan.plan_id, step_log)
                self.memory.update_status(plan.plan_id, AgentPlanStatus.NEEDS_REVIEW)

                return _result_from_plan(
                    plan_id=plan.plan_id,
                    status=AgentPlanStatus.NEEDS_REVIEW,
                    user_message=step_log.user_message,
                    outputs=outputs,
                    memory=self.memory,
                )

            try:
                tool = self.tool_registry.get(step.tool_name)
                tool_result = tool.run(
                    ToolExecutionRequest(
                        context=ToolExecutionContext(
                            workspace_id=request.workspace_id,
                            user_id=request.user_id,
                            plan_id=plan.plan_id,
                            step_id=step.step_id,
                        ),
                        payload=step.payload,
                    )
                )
                ensure_tool_result_scoped(
                    workspace_id=request.workspace_id,
                    result=tool_result,
                )

            except (ToolRegistryError, TenantScopeError, Exception) as exc:
                step_log = AgentStepLog(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status=ToolExecutionStatus.FAILED.value,
                    user_message=_readable_error_message(step.tool_name, exc),
                    error=str(exc),
                    output={"workspace_id": request.workspace_id},
                )
                self.memory.record_step(plan.plan_id, step_log)
                self.memory.update_status(plan.plan_id, AgentPlanStatus.FAILED)

                return _result_from_plan(
                    plan_id=plan.plan_id,
                    status=AgentPlanStatus.FAILED,
                    user_message=step_log.user_message,
                    outputs=outputs,
                    memory=self.memory,
                )

            step_log = _step_log_from_tool_result(
                step_id=step.step_id,
                result=tool_result,
            )
            self.memory.record_step(plan.plan_id, step_log)
            outputs.append(tool_result.output)

            if tool_result.status == ToolExecutionStatus.FAILED:
                self.memory.update_status(plan.plan_id, AgentPlanStatus.FAILED)

                return _result_from_plan(
                    plan_id=plan.plan_id,
                    status=AgentPlanStatus.FAILED,
                    user_message=tool_result.user_message,
                    outputs=outputs,
                    memory=self.memory,
                )

        self.memory.update_status(plan.plan_id, AgentPlanStatus.SUCCEEDED)

        return _result_from_plan(
            plan_id=plan.plan_id,
            status=AgentPlanStatus.SUCCEEDED,
            user_message="Agent plan completed successfully.",
            outputs=outputs,
            memory=self.memory,
        )


def _step_log_from_tool_result(
    step_id: str,
    result: ToolExecutionResult,
) -> AgentStepLog:
    return AgentStepLog(
        step_id=step_id,
        tool_name=result.tool_name,
        status=result.status.value,
        user_message=result.user_message,
        error=result.error,
        output=result.output,
    )


def _result_from_plan(
    plan_id: str,
    status: AgentPlanStatus,
    user_message: str,
    outputs: list[dict[str, Any]],
    memory: InMemoryAgentMemory,
) -> AgentRunResult:
    plan = memory.get_plan(plan_id)

    return AgentRunResult(
        plan_id=plan_id,
        status=status,
        user_message=user_message,
        outputs=outputs,
        step_logs=plan.step_logs,
    )


def _readable_error_message(tool_name: str, exc: Exception) -> str:
    return f"Tool '{tool_name}' failed safely: {exc}"
