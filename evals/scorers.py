import re
from typing import Any

from app.answers.citations import extract_source_refs
from app.answers.generator import GroundedAnswerGenerator
from app.answers.types import GroundedAnswer
from app.extraction.runner import LocalStructuredExtractionClient, StructuredExtractionRunner
from app.extraction.schemas import (
    ExtractionFieldSpec,
    ExtractionFieldType,
    ExtractionSchema,
)
from app.llm.client import LocalGroundedLLMClient
from app.retrieval.types import RetrievedChunk
from evals.schemas import (
    EvalCaseResult,
    EvalSuiteResult,
    ExtractionEvalCase,
    QAEvalCase,
)

_NO_ANSWER_PREFIX = "I don't have enough evidence"


def score_qa_case(case: QAEvalCase) -> EvalCaseResult:
    answer = _generate_answer(case)
    errors: list[str] = []

    if case.expect_no_answer:
        if not answer.message.startswith(_NO_ANSWER_PREFIX):
            errors.append("Expected no-answer response.")
        if answer.citations:
            errors.append("No-answer response should not contain citations.")

        return _case_result(
            case_id=case.id,
            errors=errors,
            metadata={
                "message": answer.message,
                "citations": [citation.source_id for citation in answer.citations],
            },
        )

    normalized_message = _normalize_text(answer.message)

    for term in case.required_answer_terms:
        if _normalize_text(term) not in normalized_message:
            errors.append(f"Missing required answer term: {term}")

    cited_refs = extract_source_refs(answer.message)

    for source_id in case.required_citations:
        if source_id not in cited_refs:
            errors.append(f"Missing required citation: {source_id}")

    known_source_ids = {source.source_id for source in case.sources}
    unknown_citations = sorted(set(cited_refs) - known_source_ids)

    if unknown_citations:
        errors.append(f"Unknown citations found: {unknown_citations}")

    if answer.review_flags:
        errors.append(f"Unexpected review flags: {answer.review_flags}")

    return _case_result(
        case_id=case.id,
        errors=errors,
        metadata={
            "message": answer.message,
            "citations": cited_refs,
            "confidence": answer.confidence,
        },
    )


def score_extraction_case(case: ExtractionEvalCase) -> EvalCaseResult:
    schema = ExtractionSchema(
        name=case.schema_name,
        fields=[
            ExtractionFieldSpec(
                name=field.name,
                description=f"Extract {field.name}",
                field_type=ExtractionFieldType(field.field_type),
            )
            for field in case.fields
        ],
    )

    runner = StructuredExtractionRunner(LocalStructuredExtractionClient())
    result = runner.extract(
        schema=schema,
        sources=[
            _answer_source_dict(
                text=case.source_text,
            )
        ],
    )

    actual_by_name = {field.name: field for field in result.fields}

    errors: list[str] = []

    for expected_field in case.fields:
        actual = actual_by_name.get(expected_field.name)

        if actual is None:
            errors.append(f"Missing extracted field: {expected_field.name}")
            continue

        if _normalize_value(actual.value) != _normalize_value(expected_field.expected_value):
            errors.append(
                f"Field {expected_field.name} mismatch: "
                f"expected={expected_field.expected_value!r}, actual={actual.value!r}"
            )

        if actual.value not in {None, ""} and actual.evidence is None:
            errors.append(f"Field {expected_field.name} is missing evidence.")

    return _case_result(
        case_id=case.id,
        errors=errors,
        metadata={
            "fields": [
                {
                    "name": field.name,
                    "value": field.value,
                    "confidence": field.confidence,
                    "review_flags": field.review_flags,
                }
                for field in result.fields
            ]
        },
    )


def suite_result(
    suite_name: str,
    case_results: list[EvalCaseResult],
) -> EvalSuiteResult:
    total = len(case_results)
    passed = sum(1 for result in case_results if result.passed)
    score = passed / total if total else 0.0

    return EvalSuiteResult(
        suite_name=suite_name,
        passed=passed == total,
        score=score,
        total_cases=total,
        passed_cases=passed,
        failed_cases=total - passed,
        case_results=case_results,
    )


def _generate_answer(case: QAEvalCase) -> GroundedAnswer:
    generator = GroundedAnswerGenerator(LocalGroundedLLMClient())

    return generator.generate(
        query=case.query,
        retrieved_chunks=[_source_to_retrieved_chunk(source) for source in case.sources],
    )


def _source_to_retrieved_chunk(source) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        workspace_id=source.workspace_id,
        text=source.text,
        source_page=source.source_page,
        source_start_offset=source.source_start_offset,
        source_end_offset=source.source_end_offset,
        vector_score=source.score,
        rerank_score=source.score,
        final_score=source.score,
        metadata=source.metadata,
    )


def _answer_source_dict(text: str) -> dict[str, Any]:
    return {
        "source_id": "S1",
        "chunk_id": "chunk-extraction-1",
        "document_id": "doc-extraction",
        "workspace_id": "workspace-eval",
        "text": text,
        "source_page": None,
        "source_start_offset": 0,
        "source_end_offset": len(text),
        "score": 0.9,
        "metadata": {"filename": "extraction.txt"},
    }


def _case_result(
    case_id: str,
    errors: list[str],
    metadata: dict[str, Any],
) -> EvalCaseResult:
    return EvalCaseResult(
        id=case_id,
        passed=not errors,
        score=1.0 if not errors else 0.0,
        errors=errors,
        metadata=metadata,
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip())


def _normalize_value(value: Any) -> str:
    if value is None:
        return ""

    return _normalize_text(str(value).rstrip("."))
