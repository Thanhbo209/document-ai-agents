import pytest

from app.agent.tools.compare import DocumentComparisonTool, DocumentSide
from app.answers.types import AnswerSource
from app.reports.exporters import export_report_markdown
from app.reports.generator import ComparisonReportGenerator, UnknownReportSectionError


def make_source(
    source_id: str,
    document_id: str,
    text: str,
) -> AnswerSource:
    return AnswerSource(
        source_id=source_id,
        chunk_id=f"{document_id}-{source_id}",
        document_id=document_id,
        workspace_id="workspace-1",
        text=text,
        source_page=1,
        source_start_offset=0,
        source_end_offset=len(text),
        score=0.9,
        metadata={"filename": f"{document_id}.txt"},
    )


def make_comparison():
    tool = DocumentComparisonTool()

    return tool.compare(
        left=DocumentSide(
            label="Original",
            document_id="doc-a",
            sources=[
                make_source(
                    source_id="S1",
                    document_id="doc-a",
                    text="Renewal date: 2026-07-01.\nAmount: $1,200.00.",
                )
            ],
        ),
        right=DocumentSide(
            label="Revised",
            document_id="doc-b",
            sources=[
                make_source(
                    source_id="S2",
                    document_id="doc-b",
                    text="Renewal date: 2027-07-01.\nAmount: $1,200.00.",
                )
            ],
        ),
        fields=["renewal_date", "amount"],
    )


def test_comparison_report_includes_sections_and_evidence_appendix() -> None:
    generator = ComparisonReportGenerator()
    comparison = make_comparison()

    report = generator.generate(comparison)

    section_ids = [section.section_id for section in report.sections]

    assert report.title == "Comparison Report: Original vs Revised"
    assert section_ids == [
        "executive_summary",
        "side_by_side_comparison",
        "evidence_appendix",
        "review_flags",
    ]
    assert report.metadata["prompt_id"] == "comparison-report-v1"
    assert report.metadata["left_document_id"] == "doc-a"
    assert report.metadata["right_document_id"] == "doc-b"
    assert len(report.evidence_appendix) == 2


def test_report_generator_can_regenerate_single_section() -> None:
    generator = ComparisonReportGenerator()
    comparison = make_comparison()

    section = generator.generate_section(
        comparison=comparison,
        section_id="side_by_side_comparison",
    )

    assert section.title == "Side-by-Side Comparison"
    assert "| Field | Status | Left Value | Right Value | Evidence |" in section.content
    assert "renewal_date" in section.content
    assert "Original:S1" in section.content
    assert "Revised:S2" in section.content


def test_report_generator_rejects_unknown_section() -> None:
    generator = ComparisonReportGenerator()
    comparison = make_comparison()

    with pytest.raises(UnknownReportSectionError, match="Unknown report section"):
        generator.generate_section(
            comparison=comparison,
            section_id="bad_section",
        )


def test_export_report_markdown() -> None:
    generator = ComparisonReportGenerator()
    comparison = make_comparison()
    report = generator.generate(comparison)

    markdown = export_report_markdown(report)

    assert markdown.startswith("# Comparison Report: Original vs Revised")
    assert "## Executive Summary" in markdown
    assert "## Side-by-Side Comparison" in markdown
    assert "## Evidence Appendix" in markdown
    assert "doc-a" in markdown
    assert "doc-b" in markdown
