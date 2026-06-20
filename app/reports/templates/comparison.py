from app.answers.types import AnswerSource

COMPARISON_PROMPT_ID = "comparison-report-v1"

COMPARISON_SECTION_ORDER = [
    "executive_summary",
    "side_by_side_comparison",
    "evidence_appendix",
    "review_flags",
]


def render_side_by_side_comparison_prompt(
    query: str,
    left_label: str,
    right_label: str,
    left_sources: list[AnswerSource],
    right_sources: list[AnswerSource],
) -> str:
    left_context = "\n\n".join(_format_source(source) for source in left_sources)
    right_context = "\n\n".join(_format_source(source) for source in right_sources)

    return f"""You are comparing two documents.

Rules:
1. Compare only using the provided sources.
2. Every comparison point must cite evidence from the relevant document.
3. When a field exists in both documents, cite both sides.
4. When a field exists in only one document, clearly mark it as missing on the other side.
5. Do not use outside knowledge.

User request:
{query}

Left document: {left_label}
{left_context}

Right document: {right_label}
{right_context}

Return a side-by-side comparison.
"""


def _format_source(source: AnswerSource) -> str:
    location_parts = []

    if source.source_page is not None:
        location_parts.append(f"page={source.source_page}")

    if source.source_start_offset is not None and source.source_end_offset is not None:
        location_parts.append(f"offsets={source.source_start_offset}-{source.source_end_offset}")

    location = ", ".join(location_parts) if location_parts else "location=unknown"

    return (
        f"[{source.source_id}] "
        f"document_id={source.document_id}, chunk_id={source.chunk_id}, {location}\n"
        f"{source.text}"
    )
