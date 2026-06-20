from app.answers.types import AnswerSource

GROUNDED_ANSWER_PROMPT_ID = "grounded-answer-v1"


def render_grounded_answer_prompt(
    query: str,
    sources: list[AnswerSource],
) -> str:
    context = "\n\n".join(_format_source(source) for source in sources)

    return f"""You are a grounded document-answering assistant.

Rules:
1. Answer only using the provided sources.
2. Every factual claim must include a citation like [S1].
3. If the sources do not contain enough evidence, say:
   "I don't have enough evidence in the provided sources to answer that."
4. Do not use outside knowledge.

Question:
{query}

Sources:
{context}

Answer:
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
