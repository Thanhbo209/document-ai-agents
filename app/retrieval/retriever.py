from dataclasses import dataclass

from app.embeddings.embedder import Embedder
from app.embeddings.types import EmbeddingInput
from app.retrieval.filters import RetrievalFilters
from app.retrieval.reranker import Reranker
from app.retrieval.types import RetrievedChunk
from app.storage.collections import workspace_collection_name
from app.storage.vector_store import VectorSearchResult, VectorStore


@dataclass(frozen=True)
class RetrievalRequest:
    workspace_id: str
    query: str
    top_k: int = 5
    filters: RetrievalFilters | None = None


class Retriever:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        reranker: Reranker | None = None,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.reranker = reranker

    def retrieve(self, request: RetrievalRequest) -> list[RetrievedChunk]:
        if request.top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        query_embedding = self.embedder.embed_batch(
            [
                EmbeddingInput(
                    id="query",
                    text=request.query,
                    metadata={"workspace_id": request.workspace_id},
                )
            ]
        )[0]

        collection_name = workspace_collection_name(request.workspace_id)
        metadata_filter = request.filters.to_metadata_filter() if request.filters else {}

        # Fetch more than requested before reranking/deduping.
        raw_results = self.vector_store.search(
            collection_name=collection_name,
            query_vector=query_embedding.vector,
            top_k=request.top_k * 4,
            metadata_filter=metadata_filter,
        )

        retrieved = _dedupe_results([_to_retrieved_chunk(result) for result in raw_results])

        if self.reranker is not None:
            return self.reranker.rerank(
                query=request.query,
                results=retrieved,
                top_k=request.top_k,
            )

        return sorted(
            retrieved,
            key=lambda result: result.final_score,
            reverse=True,
        )[: request.top_k]


def _to_retrieved_chunk(result: VectorSearchResult) -> RetrievedChunk:
    metadata = result.record.metadata

    return RetrievedChunk(
        chunk_id=str(metadata["chunk_id"]),
        document_id=str(metadata["document_id"]),
        workspace_id=str(metadata["workspace_id"]),
        text=result.record.text,
        vector_score=result.score,
        rerank_score=None,
        final_score=result.score,
        source_page=_optional_int(metadata.get("source_page")),
        source_start_offset=_optional_int(metadata.get("source_start_offset")),
        source_end_offset=_optional_int(metadata.get("source_end_offset")),
        metadata=metadata,
    )


def _dedupe_results(results: list[RetrievedChunk]) -> list[RetrievedChunk]:
    best_by_chunk_id: dict[str, RetrievedChunk] = {}

    for result in results:
        current_best = best_by_chunk_id.get(result.chunk_id)

        if current_best is None or result.final_score > current_best.final_score:
            best_by_chunk_id[result.chunk_id] = result

    return list(best_by_chunk_id.values())


def _optional_int(value: object) -> int | None:
    if value is None:
        return None

    return int(value)
