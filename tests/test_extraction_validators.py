import pytest

from app.answers.types import AnswerSource
from app.extraction.schemas import ExtractionFieldSpec, ExtractionFieldType, ExtractionSchema
from app.extraction.validators import ExtractionValidationError, validate_extraction_payload


def make_source() -> AnswerSource:
    return AnswerSource(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text="Party: Acme Corp. Renewal date: 2026-07-01. Amount: $1,200.00.",
        source_page=1,
        source_start_offset=0,
        source_end_offset=70,
        score=0.9,
        metadata={"filename": "contract.pdf"},
    )


def make_schema() -> ExtractionSchema:
    return ExtractionSchema(
        name="contract_fields",
        fields=[
            ExtractionFieldSpec(
                name="party",
                description="Contract party",
                field_type=ExtractionFieldType.TEXT,
            ),
            ExtractionFieldSpec(
                name="renewal_date",
                description="Renewal date",
                field_type=ExtractionFieldType.DATE,
            ),
        ],
    )


def test_validate_extraction_payload_accepts_valid_json_with_evidence() -> None:
    result = validate_extraction_payload(
        raw_text="""
        {
          "fields": [
            {
              "name": "party",
              "value": "Acme Corp",
              "confidence": 0.8,
              "evidence": {
                "source_id": "S1",
                "quote": "Party: Acme Corp."
              },
              "review_flags": []
            },
            {
              "name": "renewal_date",
              "value": "2026-07-01",
              "confidence": 0.9,
              "evidence": {
                "source_id": "S1",
                "quote": "Renewal date: 2026-07-01."
              },
              "review_flags": []
            }
          ],
          "review_flags": []
        }
        """,
        schema=make_schema(),
        sources=[make_source()],
    )

    assert result.schema_name == "contract_fields"
    assert len(result.fields) == 2
    assert result.fields[0].evidence is not None
    assert result.fields[0].evidence.source_id == "S1"


def test_validate_extraction_payload_repairs_markdown_json_block() -> None:
    result = validate_extraction_payload(
        raw_text="""
        ```json
        {
          "fields": [
            {
              "name": "party",
              "value": "Acme Corp",
              "confidence": 0.8,
              "evidence": {
                "source_id": "S1",
                "quote": "Party: Acme Corp."
              },
              "review_flags": []
            },
            {
              "name": "renewal_date",
              "value": null,
              "confidence": 0.0,
              "evidence": null,
              "review_flags": ["missing_evidence"]
            }
          ],
          "review_flags": []
        }
        ```
        """,
        schema=make_schema(),
        sources=[make_source()],
    )

    assert result.fields[0].name == "party"


def test_validate_extraction_rejects_unknown_field() -> None:
    with pytest.raises(ExtractionValidationError, match="Unknown extracted field"):
        validate_extraction_payload(
            raw_text='{"fields": [{"name": "unknown", "value": "x"}]}',
            schema=make_schema(),
            sources=[make_source()],
        )


def test_validate_extraction_rejects_value_without_evidence() -> None:
    with pytest.raises(ExtractionValidationError, match="has value but no evidence"):
        validate_extraction_payload(
            raw_text="""
            {
              "fields": [
                {
                  "name": "party",
                  "value": "Acme Corp",
                  "confidence": 0.8,
                  "evidence": null,
                  "review_flags": []
                },
                {
                  "name": "renewal_date",
                  "value": null,
                  "confidence": 0.0,
                  "evidence": null,
                  "review_flags": []
                }
              ]
            }
            """,
            schema=make_schema(),
            sources=[make_source()],
        )


def test_validate_extraction_rejects_quote_not_in_source() -> None:
    with pytest.raises(ExtractionValidationError, match="evidence quote is not found"):
        validate_extraction_payload(
            raw_text="""
            {
              "fields": [
                {
                  "name": "party",
                  "value": "Acme Corp",
                  "confidence": 0.8,
                  "evidence": {
                    "source_id": "S1",
                    "quote": "This quote does not exist."
                  },
                  "review_flags": []
                },
                {
                  "name": "renewal_date",
                  "value": null,
                  "confidence": 0.0,
                  "evidence": null,
                  "review_flags": []
                }
              ]
            }
            """,
            schema=make_schema(),
            sources=[make_source()],
        )
