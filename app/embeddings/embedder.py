from hashlib import sha256
from typing import Protocol

from app.embeddings.types import EmbeddedText, EmbeddingInput, Vector


class Embedder(Protocol):
    model_name: str
    model_version: str
    dimensions: int

    def embed_batch(self, inputs: list[EmbeddingInput]) -> list[EmbeddedText]:
        pass


class HashEmbedder:
    model_name = "hash-embedder"
    model_version = "hash-embedder-v1"
    dimensions = 32

    def embed_batch(self, inputs: list[EmbeddingInput]) -> list[EmbeddedText]:
        return [
            EmbeddedText(
                id=item.id,
                text=item.text,
                vector=self._embed_text(item.text),
                metadata=item.metadata,
                model_name=self.model_name,
                model_version=self.model_version,
            )
            for item in inputs
        ]

    def _embed_text(self, text: str) -> Vector:
        digest = sha256(text.encode("utf-8")).digest()

        values = []
        for byte in digest[: self.dimensions]:
            values.append((byte / 127.5) - 1.0)

        return values
