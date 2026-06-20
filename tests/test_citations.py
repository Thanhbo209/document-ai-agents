import pytest

from app.answers.citations import (
    CitationValidationError,
    build_citations_from_message,
    extract_source_refs,
    validate_cited_claims,
)
from app.answers.types import AnswerSource


def make_source(source_id: str = "S1") -> AnswerSource:
    return AnswerSource(
        source_id=source_id,
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text="Refund policy allows cancellation within 14 days.",
        source_page=2,
        source_start_offset=0,
        source_end_offset=50,
        score=0.9,
        metadata={"filename": "policy.pdf"},
    )


def test_extract_source_refs_dedupes_in_order() -> None:
    refs = extract_source_refs("A claim [S1]. Another claim [S2]. Repeat [S1].")

    assert refs == ["S1", "S2"]


def test_validate_cited_claims_accepts_cited_sentence() -> None:
    validate_cited_claims("Refunds are allowed within 14 days [S1]. ")


def test_validate_cited_claims_rejects_uncited_sentence() -> None:
    with pytest.raises(CitationValidationError, match="Uncited claim detected"):
        validate_cited_claims("Refunds are allowed within 14 days.")


def test_build_citations_from_message() -> None:
    citations = build_citations_from_message(
        message="Refunds are allowed within 14 days. [S1]",
        sources=[make_source()],
    )

    assert len(citations) == 1
    assert citations[0].source_id == "S1"
    assert citations[0].chunk_id == "chunk-1"
    assert citations[0].document_id == "doc-1"
    assert citations[0].source_page == 2


def test_build_citations_rejects_unknown_source_ref() -> None:
    with pytest.raises(CitationValidationError, match="Unknown citation reference"):
        build_citations_from_message(
            message="Refunds are allowed. [S2]",
            sources=[make_source("S1")],
        )


def test_validate_cited_claims_accepts_citation_after_sentence() -> None:
    validate_cited_claims("Refunds are allowed within 14 days. [S1]")
