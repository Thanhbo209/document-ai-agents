import pytest

from app.answers.generator import GroundedAnswerGenerationError, GroundedAnswerGenerator
from app.llm.client import LocalGroundedLLMClient
from app.retrieval.types import RetrievedChunk


class UncitedLLMClient:
    model_name = "bad-uncited-client"

    def generate_answer(self, query: str, sources: list, prompt: str) -> str:
        del query, sources, prompt
        return "Refunds are allowed within 14 days."

    def stream_answer(self, query: str, sources: list, prompt: str):
        del query, sources, prompt
        yield "Refunds are allowed within 14 days."


class UnknownCitationLLMClient:
    model_name = "bad-unknown-citation-client"

    def generate_answer(self, query: str, sources: list, prompt: str) -> str:
        del query, sources, prompt
        return "Refunds are allowed within 14 days. [S99]"

    def stream_answer(self, query: str, sources: list, prompt: str):
        del query, sources, prompt
        yield "Refunds are allowed within 14 days. [S99]"


def make_retrieved_chunk(
    text: str = "Refund policy allows cancellation within 14 days.",
    final_score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text=text,
        vector_score=0.8,
        rerank_score=1.0,
        final_score=final_score,
        source_page=2,
        source_start_offset=0,
        source_end_offset=len(text),
        metadata={"filename": "policy.pdf"},
    )


def test_grounded_answer_generator_returns_cited_answer() -> None:
    generator = GroundedAnswerGenerator(LocalGroundedLLMClient())

    answer = generator.generate(
        query="What is the refund policy?",
        retrieved_chunks=[make_retrieved_chunk()],
    )

    assert "[S1]" in answer.message
    assert len(answer.citations) == 1
    assert answer.citations[0].chunk_id == "chunk-1"
    assert answer.source_list[0].source_id == "S1"
    assert answer.confidence == 0.9
    assert answer.review_flags == []
    assert answer.model_name == "local-grounded-extractive-v1"
    assert answer.prompt_id == "grounded-answer-v1"


def test_grounded_answer_generator_handles_no_sources() -> None:
    generator = GroundedAnswerGenerator(LocalGroundedLLMClient())

    answer = generator.generate(
        query="What is the refund policy?",
        retrieved_chunks=[],
    )

    assert answer.message.startswith("I don't have enough evidence")
    assert answer.citations == []
    assert answer.source_list == []
    assert answer.confidence == 0.0
    assert answer.review_flags == ["insufficient_evidence"]


def test_grounded_answer_generator_handles_no_matching_evidence() -> None:
    generator = GroundedAnswerGenerator(LocalGroundedLLMClient())

    answer = generator.generate(
        query="What is the refund policy?",
        retrieved_chunks=[
            make_retrieved_chunk(
                text="The document only discusses office opening hours.",
                final_score=0.2,
            )
        ],
    )

    assert answer.message.startswith("I don't have enough evidence")
    assert answer.citations == []
    assert answer.review_flags == ["insufficient_evidence"]


def test_grounded_answer_generator_rejects_uncited_claims() -> None:
    generator = GroundedAnswerGenerator(UncitedLLMClient())

    with pytest.raises(GroundedAnswerGenerationError, match="Uncited claim detected"):
        generator.generate(
            query="What is the refund policy?",
            retrieved_chunks=[make_retrieved_chunk()],
        )


def test_grounded_answer_generator_rejects_unknown_citations() -> None:
    generator = GroundedAnswerGenerator(UnknownCitationLLMClient())

    with pytest.raises(GroundedAnswerGenerationError, match="Unknown citation reference"):
        generator.generate(
            query="What is the refund policy?",
            retrieved_chunks=[make_retrieved_chunk()],
        )


def test_grounded_answer_generator_flags_low_confidence() -> None:
    generator = GroundedAnswerGenerator(LocalGroundedLLMClient())

    answer = generator.generate(
        query="What is the refund policy?",
        retrieved_chunks=[
            make_retrieved_chunk(
                text="Refund policy allows cancellation within 14 days.",
                final_score=0.2,
            )
        ],
    )

    assert answer.confidence == 0.2
    assert answer.review_flags == ["low_confidence"]
