from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerSource:
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    score: float
    metadata: dict


@dataclass(frozen=True)
class AnswerCitation:
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    quote: str
    metadata: dict


@dataclass(frozen=True)
class GroundedAnswer:
    message: str
    citations: list[AnswerCitation]
    source_list: list[AnswerSource]
    confidence: float
    review_flags: list[str]
    model_name: str
    prompt_id: str
