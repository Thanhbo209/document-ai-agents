from typing import Any

from pydantic import BaseModel, Field

from app.answers.types import AnswerSource


class QAEvalCase(BaseModel):
    id: str
    query: str
    sources: list[AnswerSource]
    required_answer_terms: list[str] = Field(default_factory=list)
    required_citations: list[str] = Field(default_factory=list)
    expect_no_answer: bool = False


class ExtractionFieldEvalCase(BaseModel):
    name: str
    field_type: str
    expected_value: Any


class ExtractionEvalCase(BaseModel):
    id: str
    source_text: str
    schema_name: str
    fields: list[ExtractionFieldEvalCase]


class EvalCaseResult(BaseModel):
    id: str
    passed: bool
    score: float
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalSuiteResult(BaseModel):
    suite_name: str
    passed: bool
    score: float
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_results: list[EvalCaseResult]
