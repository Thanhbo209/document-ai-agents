import pytest

from app.agent.tools.base import (
    AgentTool,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolRegistry,
    ToolRegistryError,
)


class DummyTool:
    name = "dummy"
    description = "Dummy tool"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={"workspace_id": request.context.workspace_id},
            user_message="Done.",
        )


def test_tool_registry_registers_and_gets_tool() -> None:
    registry = ToolRegistry()
    tool: AgentTool = DummyTool()

    registry.register(tool)

    assert registry.get("dummy") is tool
    assert registry.has_tool("dummy")
    assert registry.list_tools() == [tool]


def test_tool_registry_rejects_duplicate_tool() -> None:
    registry = ToolRegistry()
    registry.register(DummyTool())

    with pytest.raises(ToolRegistryError, match="Tool already registered"):
        registry.register(DummyTool())


def test_tool_registry_rejects_missing_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolRegistryError, match="Tool not registered"):
        registry.get("missing")
