from app.storage.collections import workspace_collection_name
from app.storage.memory_vector_store import InMemoryVectorStore, cosine_similarity
from app.storage.vector_store import VectorRecord


def test_workspace_collection_name_is_stable() -> None:
    assert workspace_collection_name("abc-123") == "workspace_abc_123"


def test_in_memory_vector_store_upserts_records() -> None:
    store = InMemoryVectorStore()
    collection = "workspace_1"

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[0.1, 0.2],
                text="Hello",
                metadata={"document_id": "doc-1"},
            )
        ],
    )

    records = store.list_records(collection)

    assert len(records) == 1
    assert records[0].id == "chunk-1"


def test_in_memory_vector_store_upsert_is_idempotent_by_id() -> None:
    store = InMemoryVectorStore()
    collection = "workspace_1"

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[0.1],
                text="Old",
                metadata={"document_id": "doc-1"},
            )
        ],
    )

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[0.2],
                text="New",
                metadata={"document_id": "doc-1"},
            )
        ],
    )

    records = store.list_records(collection)

    assert len(records) == 1
    assert records[0].text == "New"
    assert records[0].vector == [0.2]


def test_in_memory_vector_store_deletes_by_document_id() -> None:
    store = InMemoryVectorStore()
    collection = "workspace_1"

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[0.1],
                text="Doc 1",
                metadata={"document_id": "doc-1"},
            ),
            VectorRecord(
                id="chunk-2",
                vector=[0.2],
                text="Doc 2",
                metadata={"document_id": "doc-2"},
            ),
        ],
    )

    store.delete_by_document_id(collection, "doc-1")

    records = store.list_records(collection)

    assert len(records) == 1
    assert records[0].metadata["document_id"] == "doc-2"


def test_cosine_similarity_scores_identical_vectors_highest() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_in_memory_vector_store_search_returns_top_k_by_score() -> None:
    store = InMemoryVectorStore()
    collection = "workspace_1"

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[1.0, 0.0],
                text="Alpha",
                metadata={"document_id": "doc-1"},
            ),
            VectorRecord(
                id="chunk-2",
                vector=[0.0, 1.0],
                text="Beta",
                metadata={"document_id": "doc-2"},
            ),
        ],
    )

    results = store.search(
        collection_name=collection,
        query_vector=[1.0, 0.0],
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].record.id == "chunk-1"
    assert results[0].score == 1.0


def test_in_memory_vector_store_search_applies_metadata_filter() -> None:
    store = InMemoryVectorStore()
    collection = "workspace_1"

    store.upsert(
        collection,
        [
            VectorRecord(
                id="chunk-1",
                vector=[1.0, 0.0],
                text="Alpha",
                metadata={"document_id": "doc-1"},
            ),
            VectorRecord(
                id="chunk-2",
                vector=[1.0, 0.0],
                text="Beta",
                metadata={"document_id": "doc-2"},
            ),
        ],
    )

    results = store.search(
        collection_name=collection,
        query_vector=[1.0, 0.0],
        top_k=10,
        metadata_filter={"document_id": "doc-2"},
    )

    assert len(results) == 1
    assert results[0].record.id == "chunk-2"
