from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class ToolExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ToolRegistryError(ValueError):
    pass


class TenantScopeError(ValueError):
    pass


@dataclass(frozen=True)
class ToolExecutionContext:
    workspace_id: str
    user_id: str | None = None
    plan_id: str | None = None
    step_id: str | None = None


@dataclass(frozen=True)
class ToolExecutionRequest:
    context: ToolExecutionContext
    payload: dict[str, Any]


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    status: ToolExecutionStatus
    output: dict[str, Any]
    user_message: str
    error: str | None = None
    review_required: bool = False


class AgentTool(Protocol):
    name: str
    description: str
    requires_human_review: bool

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        if tool.name in self._tools:
            raise ToolRegistryError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool:
        tool = self._tools.get(name)

        if tool is None:
            raise ToolRegistryError(f"Tool not registered: {name}")

        return tool

    def list_tools(self) -> list[AgentTool]:
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        return name in self._tools


def ensure_tool_result_scoped(
    workspace_id: str,
    result: ToolExecutionResult,
) -> None:
    if result.status != ToolExecutionStatus.SUCCEEDED:
        return

    result_workspace_id = result.output.get("workspace_id")

    if result_workspace_id != workspace_id:
        raise TenantScopeError(f"Tool '{result.tool_name}' returned data outside workspace scope.")
