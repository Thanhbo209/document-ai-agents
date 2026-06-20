from app.agent.memory import AgentPlanStatus, InMemoryAgentMemory
from app.agent.orchestrator import AgentOrchestrator, AgentRunRequest
from app.agent.tools.base import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolRegistry,
)


class SearchDocumentsTool:
    name = "search_documents"
    description = "Search documents"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "workspace_id": request.context.workspace_id,
                "results": ["chunk-1"],
            },
            user_message="Search completed.",
        )


class SummarizeDocumentTool:
    name = "summarize_document"
    description = "Summarize document"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "workspace_id": request.context.workspace_id,
                "summary": "Document summary.",
            },
            user_message="Summary completed.",
        )


class CompareDocumentsTool:
    name = "compare_documents"
    description = "Compare documents"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "workspace_id": request.context.workspace_id,
                "comparison_id": "comparison-1",
            },
            user_message="Comparison completed.",
        )


class GenerateReportTool:
    name = "generate_report"
    description = "Generate report"
    requires_human_review = True

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "workspace_id": request.context.workspace_id,
                "report_id": "report-1",
            },
            user_message="Report generated.",
        )


class BadTenantTool:
    name = "search_documents"
    description = "Bad tenant tool"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        del request

        return ToolExecutionResult(
            tool_name=self.name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "workspace_id": "other-workspace",
                "results": ["leaked-chunk"],
            },
            user_message="Leaked data.",
        )


class CrashingTool:
    name = "search_documents"
    description = "Crashing tool"
    requires_human_review = False

    def run(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        del request
        raise RuntimeError("Vector store unavailable")


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(SearchDocumentsTool())
    registry.register(SummarizeDocumentTool())
    registry.register(CompareDocumentsTool())
    registry.register(GenerateReportTool())
    return registry


def test_orchestrator_executes_planned_search_and_logs_plan() -> None:
    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=build_registry(),
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Find refund policy",
        )
    )

    assert result.status == AgentPlanStatus.SUCCEEDED
    assert result.outputs[0]["workspace_id"] == "workspace-1"
    assert result.outputs[0]["results"] == ["chunk-1"]
    assert len(result.step_logs) == 1
    assert result.step_logs[0].tool_name == "search_documents"

    plan = memory.get_plan(result.plan_id)

    assert plan.workspace_id == "workspace-1"
    assert plan.status == AgentPlanStatus.SUCCEEDED
    assert len(plan.step_logs) == 1


def test_orchestrator_chooses_summary_tool() -> None:
    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=build_registry(),
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Summarize this document",
        )
    )

    assert result.status == AgentPlanStatus.SUCCEEDED
    assert result.step_logs[0].tool_name == "summarize_document"
    assert result.outputs[0]["summary"] == "Document summary."


def test_orchestrator_stops_at_human_review_checkpoint() -> None:
    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=build_registry(),
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Compare documents and generate report",
        )
    )

    assert result.status == AgentPlanStatus.NEEDS_REVIEW
    assert result.step_logs[-1].tool_name == "generate_report"
    assert result.step_logs[-1].status == "needs_review"
    assert "needs human review" in result.user_message


def test_orchestrator_executes_review_step_when_approved() -> None:
    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=build_registry(),
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Compare documents and generate report",
            approved_step_ids=["step-2"],
        )
    )

    assert result.status == AgentPlanStatus.SUCCEEDED
    assert [step.tool_name for step in result.step_logs] == [
        "compare_documents",
        "generate_report",
    ]
    assert result.outputs[-1]["report_id"] == "report-1"


def test_orchestrator_blocks_tool_that_bypasses_tenant_scope() -> None:
    registry = ToolRegistry()
    registry.register(BadTenantTool())

    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=registry,
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Find refund policy",
        )
    )

    assert result.status == AgentPlanStatus.FAILED
    assert "failed safely" in result.user_message
    assert "outside workspace scope" in result.step_logs[0].error


def test_orchestrator_turns_tool_crash_into_readable_failure() -> None:
    registry = ToolRegistry()
    registry.register(CrashingTool())

    memory = InMemoryAgentMemory()
    orchestrator = AgentOrchestrator(
        tool_registry=registry,
        memory=memory,
    )

    result = orchestrator.run(
        AgentRunRequest(
            workspace_id="workspace-1",
            user_request="Find refund policy",
        )
    )

    assert result.status == AgentPlanStatus.FAILED
    assert result.user_message == (
        "Tool 'search_documents' failed safely: Vector store unavailable"
    )
    assert result.step_logs[0].status == "failed"
