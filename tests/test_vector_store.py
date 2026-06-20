from app.storage.collections import workspace_collection_name
from app.storage.memory_vector_store import InMemoryVectorStore
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
