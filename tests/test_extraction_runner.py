from app.answers.types import AnswerSource
from app.extraction.runner import LocalStructuredExtractionClient, StructuredExtractionRunner
from app.extraction.schemas import ExtractionFieldSpec, ExtractionFieldType, ExtractionSchema


def make_source() -> AnswerSource:
    return AnswerSource(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text=(
            "Party: Acme Corp.\n"
            "The agreement renews on 2026-07-01.\n"
            "The total amount is $1,200.00.\n"
            "The vendor must provide support."
        ),
        source_page=1,
        source_start_offset=0,
        source_end_offset=120,
        score=0.95,
        metadata={"filename": "contract.pdf"},
    )


def test_structured_extraction_runner_extracts_fields_with_evidence() -> None:
    schema = ExtractionSchema(
        name="contract_summary",
        fields=[
            ExtractionFieldSpec(
                name="party",
                description="Main party",
                field_type=ExtractionFieldType.TEXT,
            ),
            ExtractionFieldSpec(
                name="renewal_date",
                description="Renewal date",
                field_type=ExtractionFieldType.DATE,
            ),
            ExtractionFieldSpec(
                name="amount",
                description="Contract amount",
                field_type=ExtractionFieldType.AMOUNT,
            ),
            ExtractionFieldSpec(
                name="support_required",
                description="Whether support is required",
                field_type=ExtractionFieldType.BOOLEAN,
            ),
        ],
    )

    runner = StructuredExtractionRunner(LocalStructuredExtractionClient())

    result = runner.run(
        schema=schema,
        sources=[make_source()],
    )

    values = {field.name: field for field in result.fields}

    assert values["party"].value == "Acme Corp."
    assert values["party"].evidence is not None
    assert values["renewal_date"].value == "2026-07-01"
    assert values["amount"].value == "$1,200.00"
    assert values["support_required"].value is True

    for field in result.fields:
        if field.value is not None:
            assert field.evidence is not None
            assert field.evidence.source_id == "S1"


def test_structured_extraction_runner_marks_missing_fields() -> None:
    schema = ExtractionSchema(
        name="missing_fields",
        fields=[
            ExtractionFieldSpec(
                name="termination_date",
                description="Termination date",
                field_type=ExtractionFieldType.DATE,
            )
        ],
    )
    source = AnswerSource(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text="This document has no date.",
        source_page=None,
        source_start_offset=0,
        source_end_offset=26,
        score=0.5,
        metadata={},
    )

    runner = StructuredExtractionRunner(LocalStructuredExtractionClient())

    result = runner.run(schema=schema, sources=[source])

    assert result.fields[0].value is None
    assert result.fields[0].evidence is None
    assert result.fields[0].review_flags == ["missing_evidence"]
