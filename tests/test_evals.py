from evals.schemas import ExtractionEvalCase, ExtractionFieldEvalCase, QAEvalCase
from evals.scorers import score_extraction_case, score_qa_case


def test_qa_eval_passes_when_answer_contains_terms_and_citation() -> None:
    case = QAEvalCase.model_validate(
        {
            "id": "qa_refund_policy",
            "query": "What is the refund policy?",
            "sources": [
                {
                    "source_id": "S1",
                    "chunk_id": "chunk-refund-1",
                    "document_id": "doc-refund",
                    "workspace_id": "workspace-eval",
                    "text": "Refund policy allows cancellation within 14 days.",
                    "source_page": None,
                    "source_start_offset": 0,
                    "source_end_offset": 51,
                    "score": 0.95,
                    "metadata": {},
                }
            ],
            "required_answer_terms": ["refund", "cancellation", "14 days"],
            "required_citations": ["S1"],
            "expect_no_answer": False,
        }
    )

    result = score_qa_case(case)

    assert result.passed
    assert result.score == 1.0
    assert result.errors == []


def test_qa_eval_passes_no_answer_case() -> None:
    case = QAEvalCase.model_validate(
        {
            "id": "qa_no_answer",
            "query": "What is the warranty period?",
            "sources": [
                {
                    "source_id": "S1",
                    "chunk_id": "chunk-shipping-1",
                    "document_id": "doc-shipping",
                    "workspace_id": "workspace-eval",
                    "text": "Shipping takes five business days.",
                    "source_page": None,
                    "source_start_offset": 0,
                    "source_end_offset": 34,
                    "score": 0.72,
                    "metadata": {},
                }
            ],
            "required_answer_terms": [],
            "required_citations": [],
            "expect_no_answer": True,
        }
    )

    result = score_qa_case(case)

    assert result.passed
    assert result.score == 1.0


def test_extraction_eval_scores_expected_fields() -> None:
    case = ExtractionEvalCase(
        id="extract_contract_basic_fields",
        source_text=("Party: Acme Corp.\nRenewal date: 2026-07-01.\nAmount: $1,200.00."),
        schema_name="contract_fields",
        fields=[
            ExtractionFieldEvalCase(
                name="party",
                field_type="text",
                expected_value="Acme Corp",
            ),
            ExtractionFieldEvalCase(
                name="renewal_date",
                field_type="date",
                expected_value="2026-07-01",
            ),
            ExtractionFieldEvalCase(
                name="amount",
                field_type="amount",
                expected_value="$1,200.00",
            ),
        ],
    )

    result = score_extraction_case(case)

    assert result.passed
    assert result.score == 1.0
