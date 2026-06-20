import re
from typing import Protocol

from app.retrieval.types import RetrievedChunk

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        pass


class KeywordOverlapReranker:
    def rerank(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_terms = _token_set(query)

        reranked: list[RetrievedChunk] = []

        for result in results:
            chunk_terms = _token_set(result.text)
            overlap_score = _overlap_score(query_terms, chunk_terms)
            final_score = (0.7 * result.vector_score) + (0.3 * overlap_score)

            reranked.append(
                RetrievedChunk(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    workspace_id=result.workspace_id,
                    text=result.text,
                    vector_score=result.vector_score,
                    rerank_score=overlap_score,
                    final_score=final_score,
                    source_page=result.source_page,
                    source_start_offset=result.source_start_offset,
                    source_end_offset=result.source_end_offset,
                    metadata=result.metadata,
                )
            )

        return sorted(
            reranked,
            key=lambda result: result.final_score,
            reverse=True,
        )[:top_k]


def _token_set(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(text)}


def _overlap_score(query_terms: set[str], chunk_terms: set[str]) -> float:
    if not query_terms or not chunk_terms:
        return 0.0

    return len(query_terms & chunk_terms) / len(query_terms)
