from functools import lru_cache

from app.embeddings.embedder import HashEmbedder
from app.storage.memory_vector_store import InMemoryVectorStore


@lru_cache
def get_runtime_embedder() -> HashEmbedder:
    return HashEmbedder()


@lru_cache
def get_runtime_vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()
