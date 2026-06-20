from dataclasses import dataclass
from enum import StrEnum

from app.agent.tools.compare import ComparisonItem, ComparisonResult, EvidenceRef
from app.reports.templates.comparison import COMPARISON_PROMPT_ID, COMPARISON_SECTION_ORDER


class ReportSectionId(StrEnum):
    EXECUTIVE_SUMMARY = "executive_summary"
    SIDE_BY_SIDE_COMPARISON = "side_by_side_comparison"
    EVIDENCE_APPENDIX = "evidence_appendix"
    REVIEW_FLAGS = "review_flags"


class UnknownReportSectionError(ValueError):
    pass


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    title: str
    content: str


@dataclass(frozen=True)
class GeneratedReport:
    title: str
    sections: list[ReportSection]
    evidence_appendix: list[EvidenceRef]
    metadata: dict


class ComparisonReportGenerator:
    def generate(
        self,
        comparison: ComparisonResult,
    ) -> GeneratedReport:
        sections = [
            self.generate_section(
                comparison=comparison,
                section_id=section_id,
            )
            for section_id in COMPARISON_SECTION_ORDER
        ]

        return GeneratedReport(
            title=(f"Comparison Report: {comparison.left_label} vs {comparison.right_label}"),
            sections=sections,
            evidence_appendix=comparison.evidence_appendix,
            metadata={
                "prompt_id": COMPARISON_PROMPT_ID,
                "left_document_id": comparison.left_document_id,
                "right_document_id": comparison.right_document_id,
                "left_label": comparison.left_label,
                "right_label": comparison.right_label,
                "section_count": len(sections),
            },
        )

    def generate_section(
        self,
        comparison: ComparisonResult,
        section_id: str,
    ) -> ReportSection:
        if section_id == ReportSectionId.EXECUTIVE_SUMMARY:
            return _executive_summary_section(comparison)

        if section_id == ReportSectionId.SIDE_BY_SIDE_COMPARISON:
            return _side_by_side_section(comparison)

        if section_id == ReportSectionId.EVIDENCE_APPENDIX:
            return _evidence_appendix_section(comparison)

        if section_id == ReportSectionId.REVIEW_FLAGS:
            return _review_flags_section(comparison)

        raise UnknownReportSectionError(f"Unknown report section: {section_id}")


def _executive_summary_section(comparison: ComparisonResult) -> ReportSection:
    total = len(comparison.items)
    changed = _count_items(comparison.items, "changed")
    same = _count_items(comparison.items, "same")
    only_left = _count_items(comparison.items, "only_left")
    only_right = _count_items(comparison.items, "only_right")

    lines = [
        f"Compared **{comparison.left_label}** against **{comparison.right_label}**.",
        "",
        f"- Total comparison points: {total}",
        f"- Same: {same}",
        f"- Changed: {changed}",
        f"- Only in {comparison.left_label}: {only_left}",
        f"- Only in {comparison.right_label}: {only_right}",
    ]

    if comparison.review_flags:
        lines.append("")
        lines.append(f"Review flags: {', '.join(comparison.review_flags)}.")

    return ReportSection(
        section_id=ReportSectionId.EXECUTIVE_SUMMARY.value,
        title="Executive Summary",
        content="\n".join(lines),
    )


def _side_by_side_section(comparison: ComparisonResult) -> ReportSection:
    rows = [
        "| Field | Status | Left Value | Right Value | Evidence |",
        "|---|---|---|---|---|",
    ]

    for item in comparison.items:
        rows.append(
            "| "
            f"{_escape_table(item.key)} | "
            f"{item.status.value} | "
            f"{_escape_table(item.left_value or '')} | "
            f"{_escape_table(item.right_value or '')} | "
            f"{_escape_table(_evidence_label(item))} |"
        )

    return ReportSection(
        section_id=ReportSectionId.SIDE_BY_SIDE_COMPARISON.value,
        title="Side-by-Side Comparison",
        content="\n".join(rows),
    )


def _evidence_appendix_section(comparison: ComparisonResult) -> ReportSection:
    lines = []

    for evidence in comparison.evidence_appendix:
        location = _format_location(evidence)
        lines.append(
            f"- **{evidence.side}:{evidence.source_id}** "
            f"document=`{evidence.document_id}`, chunk=`{evidence.chunk_id}`, "
            f"{location}\n"
            f"  > {evidence.quote}"
        )

    return ReportSection(
        section_id=ReportSectionId.EVIDENCE_APPENDIX.value,
        title="Evidence Appendix",
        content="\n".join(lines),
    )


def _review_flags_section(comparison: ComparisonResult) -> ReportSection:
    if not comparison.review_flags:
        content = "No review flags."
    else:
        content = "\n".join(f"- {flag}" for flag in comparison.review_flags)

    return ReportSection(
        section_id=ReportSectionId.REVIEW_FLAGS.value,
        title="Review Flags",
        content=content,
    )


def _count_items(items: list[ComparisonItem], status: str) -> int:
    return sum(1 for item in items if item.status.value == status)


def _evidence_label(item: ComparisonItem) -> str:
    labels = []

    if item.left_evidence is not None:
        labels.append(f"{item.left_evidence.side}:{item.left_evidence.source_id}")

    if item.right_evidence is not None:
        labels.append(f"{item.right_evidence.side}:{item.right_evidence.source_id}")

    return ", ".join(labels)


def _format_location(evidence: EvidenceRef) -> str:
    parts = []

    if evidence.source_page is not None:
        parts.append(f"page={evidence.source_page}")

    if evidence.source_start_offset is not None and evidence.source_end_offset is not None:
        parts.append(f"offsets={evidence.source_start_offset}-{evidence.source_end_offset}")

    return ", ".join(parts) if parts else "location=unknown"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
