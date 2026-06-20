from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    vector_score: float
    rerank_score: float | None
    final_score: float
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    metadata: dict
