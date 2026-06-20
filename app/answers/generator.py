from app.answers.citations import (
    CitationValidationError,
    build_citations_from_message,
    validate_cited_claims,
)
from app.answers.types import AnswerSource, GroundedAnswer
from app.llm.client import LLMClient
from app.llm.prompts import GROUNDED_ANSWER_PROMPT_ID, render_grounded_answer_prompt
from app.retrieval.types import RetrievedChunk

NO_ANSWER_MESSAGE = "I don't have enough evidence in the provided sources to answer that."


class GroundedAnswerGenerationError(ValueError):
    pass


class GroundedAnswerGenerator:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> GroundedAnswer:
        sources = _sources_from_retrieved_chunks(retrieved_chunks)

        if not sources:
            return _no_answer(self.llm_client.model_name)

        prompt = render_grounded_answer_prompt(
            query=query,
            sources=sources,
        )

        message = self.llm_client.generate_answer(
            query=query,
            sources=sources,
            prompt=prompt,
        ).strip()

        if _is_no_answer(message):
            return _no_answer(self.llm_client.model_name, sources=sources)

        try:
            validate_cited_claims(message)
            citations = build_citations_from_message(message, sources)
        except CitationValidationError as exc:
            raise GroundedAnswerGenerationError(str(exc)) from exc

        if not citations:
            raise GroundedAnswerGenerationError("Answer must include at least one citation.")

        confidence = _confidence_for_citations(citations, sources)
        review_flags = _review_flags(confidence)

        return GroundedAnswer(
            message=message,
            citations=citations,
            source_list=sources,
            confidence=confidence,
            review_flags=review_flags,
            model_name=self.llm_client.model_name,
            prompt_id=GROUNDED_ANSWER_PROMPT_ID,
        )


def _sources_from_retrieved_chunks(
    chunks: list[RetrievedChunk],
) -> list[AnswerSource]:
    sources: list[AnswerSource] = []

    for index, chunk in enumerate(chunks, start=1):
        sources.append(
            AnswerSource(
                source_id=f"S{index}",
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                workspace_id=chunk.workspace_id,
                text=chunk.text,
                source_page=chunk.source_page,
                source_start_offset=chunk.source_start_offset,
                source_end_offset=chunk.source_end_offset,
                score=chunk.final_score,
                metadata=chunk.metadata,
            )
        )

    return sources


def _no_answer(
    model_name: str,
    sources: list[AnswerSource] | None = None,
) -> GroundedAnswer:
    return GroundedAnswer(
        message=NO_ANSWER_MESSAGE,
        citations=[],
        source_list=sources or [],
        confidence=0.0,
        review_flags=["insufficient_evidence"],
        model_name=model_name,
        prompt_id=GROUNDED_ANSWER_PROMPT_ID,
    )


def _is_no_answer(message: str) -> bool:
    return message.lower().startswith("i don't have enough evidence")


def _confidence_for_citations(
    citations: list,
    sources: list[AnswerSource],
) -> float:
    cited_source_ids = {citation.source_id for citation in citations}
    cited_scores = [source.score for source in sources if source.source_id in cited_source_ids]

    if not cited_scores:
        return 0.0

    return sum(cited_scores) / len(cited_scores)


def _review_flags(confidence: float) -> list[str]:
    flags: list[str] = []

    if confidence < 0.3:
        flags.append("low_confidence")

    return flags
