from app.embeddings.embedder import HashEmbedder
from app.embeddings.types import EmbeddingInput


def test_hash_embedder_is_deterministic() -> None:
    embedder = HashEmbedder()

    inputs = [
        EmbeddingInput(
            id="chunk-1",
            text="Hello world",
            metadata={"document_id": "doc-1"},
        )
    ]

    first = embedder.embed_batch(inputs)
    second = embedder.embed_batch(inputs)

    assert first[0].vector == second[0].vector
    assert first[0].model_name == "hash-embedder"
    assert first[0].model_version == "hash-embedder-v1"
    assert len(first[0].vector) == 32


def test_hash_embedder_changes_when_text_changes() -> None:
    embedder = HashEmbedder()

    first = embedder.embed_batch([EmbeddingInput(id="1", text="Alpha", metadata={})])
    second = embedder.embed_batch([EmbeddingInput(id="1", text="Beta", metadata={})])

    assert first[0].vector != second[0].vector
