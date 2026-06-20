import pytest

from app.agent.tools.compare import (
    ComparisonInputError,
    ComparisonStatus,
    DocumentComparisonTool,
    DocumentSide,
)
from app.answers.types import AnswerSource


def make_source(
    source_id: str,
    document_id: str,
    text: str,
    source_page: int | None = 1,
) -> AnswerSource:
    return AnswerSource(
        source_id=source_id,
        chunk_id=f"{document_id}-{source_id}",
        document_id=document_id,
        workspace_id="workspace-1",
        text=text,
        source_page=source_page,
        source_start_offset=0,
        source_end_offset=len(text),
        score=0.9,
        metadata={"filename": f"{document_id}.txt"},
    )


def test_compare_detects_same_and_changed_fields_with_evidence() -> None:
    tool = DocumentComparisonTool()

    left = DocumentSide(
        label="Original",
        document_id="doc-a",
        sources=[
            make_source(
                source_id="S1",
                document_id="doc-a",
                text="Renewal date: 2026-07-01.\nAmount: $1,200.00.",
            )
        ],
    )
    right = DocumentSide(
        label="Revised",
        document_id="doc-b",
        sources=[
            make_source(
                source_id="S2",
                document_id="doc-b",
                text="Renewal date: 2027-07-01.\nAmount: $1,200.00.",
            )
        ],
    )

    result = tool.compare(
        left=left,
        right=right,
        fields=["renewal_date", "amount"],
    )

    by_key = {item.key: item for item in result.items}

    assert by_key["renewal_date"].status == ComparisonStatus.CHANGED
    assert by_key["renewal_date"].left_value == "2026-07-01"
    assert by_key["renewal_date"].right_value == "2027-07-01"
    assert by_key["renewal_date"].left_evidence is not None
    assert by_key["renewal_date"].right_evidence is not None

    assert by_key["amount"].status == ComparisonStatus.SAME
    assert by_key["amount"].left_evidence is not None
    assert by_key["amount"].right_evidence is not None

    appendix_document_ids = {evidence.document_id for evidence in result.evidence_appendix}

    assert appendix_document_ids == {"doc-a", "doc-b"}
    assert "differences_found" in result.review_flags


def test_compare_detects_field_only_in_left_document() -> None:
    tool = DocumentComparisonTool()

    left = DocumentSide(
        label="Original",
        document_id="doc-a",
        sources=[
            make_source(
                source_id="S1",
                document_id="doc-a",
                text="Termination fee: $500.00.",
            )
        ],
    )
    right = DocumentSide(
        label="Revised",
        document_id="doc-b",
        sources=[
            make_source(
                source_id="S2",
                document_id="doc-b",
                text="Renewal date: 2027-07-01.",
            )
        ],
    )

    result = tool.compare(
        left=left,
        right=right,
        fields=["termination_fee"],
    )

    assert len(result.items) == 1
    assert result.items[0].status == ComparisonStatus.ONLY_LEFT
    assert result.items[0].left_value == "$500.00"
    assert result.items[0].right_value is None
    assert result.items[0].left_evidence is not None
    assert result.items[0].right_evidence is None
    assert "missing_fields_found" in result.review_flags


def test_compare_rejects_missing_sources() -> None:
    tool = DocumentComparisonTool()

    left = DocumentSide(
        label="Original",
        document_id="doc-a",
        sources=[],
    )
    right = DocumentSide(
        label="Revised",
        document_id="doc-b",
        sources=[
            make_source(
                source_id="S2",
                document_id="doc-b",
                text="Amount: $1,200.00.",
            )
        ],
    )

    with pytest.raises(ComparisonInputError, match="must include at least one source"):
        tool.compare(left=left, right=right)


def test_compare_rejects_source_from_wrong_document() -> None:
    tool = DocumentComparisonTool()

    left = DocumentSide(
        label="Original",
        document_id="doc-a",
        sources=[
            make_source(
                source_id="S1",
                document_id="doc-wrong",
                text="Amount: $1,200.00.",
            )
        ],
    )
    right = DocumentSide(
        label="Revised",
        document_id="doc-b",
        sources=[
            make_source(
                source_id="S2",
                document_id="doc-b",
                text="Amount: $1,200.00.",
            )
        ],
    )

    with pytest.raises(ComparisonInputError, match="does not belong"):
        tool.compare(left=left, right=right)
