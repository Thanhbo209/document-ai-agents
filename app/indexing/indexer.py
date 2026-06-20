from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.embeddings.embedder import Embedder
from app.embeddings.types import EmbeddingInput
from app.repositories.documents import DocumentRepository
from app.storage.collections import workspace_collection_name
from app.storage.vector_store import VectorRecord, VectorStore


@dataclass(frozen=True)
class IndexDocumentResult:
    workspace_id: str
    document_id: str
    collection_name: str
    chunks_indexed: int
    embedding_model_name: str
    embedding_model_version: str


class DocumentIndexer:
    def __init__(
        self,
        db: Session,
        embedder: Embedder,
        vector_store: VectorStore,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.vector_store = vector_store

    def index_document(
        self,
        workspace_id: str,
        document_id: str,
    ) -> IndexDocumentResult:
        document_repo = DocumentRepository(self.db)
        chunks = document_repo.list_chunks_for_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )

        collection_name = workspace_collection_name(workspace_id)

        self.vector_store.delete_by_document_id(
            collection_name=collection_name,
            document_id=document_id,
        )

        embedding_inputs = [
            EmbeddingInput(
                id=chunk.id,
                text=chunk.text,
                metadata={
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "source_page": chunk.source_page,
                    "source_start_offset": chunk.source_start_offset,
                    "source_end_offset": chunk.source_end_offset,
                    "source_metadata": chunk.source_metadata,
                },
            )
            for chunk in chunks
        ]

        embedded_chunks = self.embedder.embed_batch(embedding_inputs)

        records = [
            VectorRecord(
                id=embedded.id,
                vector=embedded.vector,
                text=embedded.text,
                metadata={
                    **embedded.metadata,
                    "embedding_model_name": embedded.model_name,
                    "embedding_model_version": embedded.model_version,
                },
            )
            for embedded in embedded_chunks
        ]

        self.vector_store.upsert(
            collection_name=collection_name,
            records=records,
        )

        return IndexDocumentResult(
            workspace_id=workspace_id,
            document_id=document_id,
            collection_name=collection_name,
            chunks_indexed=len(records),
            embedding_model_name=self.embedder.model_name,
            embedding_model_version=self.embedder.model_version,
        )
