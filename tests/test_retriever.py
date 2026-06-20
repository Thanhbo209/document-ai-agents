from app.embeddings.embedder import HashEmbedder
from app.retrieval.filters import RetrievalFilters
from app.retrieval.reranker import KeywordOverlapReranker
from app.retrieval.retriever import RetrievalRequest, Retriever
from app.storage.collections import workspace_collection_name
from app.storage.memory_vector_store import InMemoryVectorStore
from app.storage.vector_store import VectorRecord


def add_record(
    store: InMemoryVectorStore,
    workspace_id: str,
    chunk_id: str,
    document_id: str,
    text: str,
    vector: list[float],
    source_page: int | None = None,
) -> None:
    store.upsert(
        workspace_collection_name(workspace_id),
        [
            VectorRecord(
                id=chunk_id,
                vector=vector,
                text=text,
                metadata={
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": 0,
                    "source_page": source_page,
                    "source_start_offset": 0,
                    "source_end_offset": len(text),
                    "source_metadata": {"filename": "notes.txt"},
                    "embedding_model_name": "test-embedder",
                    "embedding_model_version": "test-v1",
                },
            )
        ],
    )


class StaticQueryEmbedder(HashEmbedder):
    model_name = "static-query-embedder"
    model_version = "static-query-embedder-v1"
    dimensions = 2

    def _embed_text(self, text: str) -> list[float]:
        if "refund" in text.lower():
            return [1.0, 0.0]

        return [0.0, 1.0]


def test_retriever_returns_relevant_chunks_with_traceable_scores() -> None:
    store = InMemoryVectorStore()
    workspace_id = "workspace-a"

    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-refund",
        document_id="doc-1",
        text="Refund policy allows cancellation within 14 days.",
        vector=[1.0, 0.0],
        source_page=2,
    )
    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-shipping",
        document_id="doc-1",
        text="Shipping takes five business days.",
        vector=[0.0, 1.0],
        source_page=5,
    )

    retriever = Retriever(
        embedder=StaticQueryEmbedder(),
        vector_store=store,
        reranker=KeywordOverlapReranker(),
    )

    results = retriever.retrieve(
        RetrievalRequest(
            workspace_id=workspace_id,
            query="What is the refund policy?",
            top_k=1,
        )
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-refund"
    assert results[0].document_id == "doc-1"
    assert results[0].workspace_id == workspace_id
    assert results[0].source_page == 2
    assert results[0].vector_score > 0
    assert results[0].rerank_score is not None
    assert results[0].final_score > 0


def test_retriever_scopes_queries_to_workspace_collection() -> None:
    store = InMemoryVectorStore()

    add_record(
        store=store,
        workspace_id="workspace-a",
        chunk_id="chunk-a",
        document_id="doc-a",
        text="Refund policy in workspace A.",
        vector=[1.0, 0.0],
    )
    add_record(
        store=store,
        workspace_id="workspace-b",
        chunk_id="chunk-b",
        document_id="doc-b",
        text="Refund policy in workspace B.",
        vector=[1.0, 0.0],
    )

    retriever = Retriever(
        embedder=StaticQueryEmbedder(),
        vector_store=store,
    )

    results = retriever.retrieve(
        RetrievalRequest(
            workspace_id="workspace-a",
            query="refund",
            top_k=10,
        )
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-a"
    assert results[0].workspace_id == "workspace-a"


def test_retriever_applies_document_filters() -> None:
    store = InMemoryVectorStore()
    workspace_id = "workspace-a"

    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-1",
        document_id="doc-1",
        text="Refund policy from doc one.",
        vector=[1.0, 0.0],
    )
    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-2",
        document_id="doc-2",
        text="Refund policy from doc two.",
        vector=[1.0, 0.0],
    )

    retriever = Retriever(
        embedder=StaticQueryEmbedder(),
        vector_store=store,
    )

    results = retriever.retrieve(
        RetrievalRequest(
            workspace_id=workspace_id,
            query="refund",
            top_k=10,
            filters=RetrievalFilters(document_ids=["doc-2"]),
        )
    )

    assert len(results) == 1
    assert results[0].document_id == "doc-2"


def test_retriever_respects_top_k() -> None:
    store = InMemoryVectorStore()
    workspace_id = "workspace-a"

    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-1",
        document_id="doc-1",
        text="Refund policy one.",
        vector=[1.0, 0.0],
    )
    add_record(
        store=store,
        workspace_id=workspace_id,
        chunk_id="chunk-2",
        document_id="doc-2",
        text="Refund policy two.",
        vector=[1.0, 0.0],
    )

    retriever = Retriever(
        embedder=StaticQueryEmbedder(),
        vector_store=store,
    )

    results = retriever.retrieve(
        RetrievalRequest(
            workspace_id=workspace_id,
            query="refund",
            top_k=1,
        )
    )

    assert len(results) == 1


def test_retriever_rejects_invalid_top_k() -> None:
    retriever = Retriever(
        embedder=StaticQueryEmbedder(),
        vector_store=InMemoryVectorStore(),
    )

    try:
        retriever.retrieve(
            RetrievalRequest(
                workspace_id="workspace-a",
                query="refund",
                top_k=0,
            )
        )
    except ValueError as exc:
        assert str(exc) == "top_k must be greater than 0."
    else:
        raise AssertionError("Expected ValueError")
