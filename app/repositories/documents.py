from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, IngestionJob
from app.models.enums import DocumentStatus, JobStatus


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_document(
        self,
        workspace_id: str,
        title: str,
        source_type: str,
        status: DocumentStatus = DocumentStatus.CREATED,
    ) -> Document:
        document = Document(
            workspace_id=workspace_id,
            title=title,
            source_type=source_type,
            status=status.value,
        )
        self.db.add(document)
        self.db.flush()
        return document

    def get_document_for_workspace(
        self,
        document_id: str,
        workspace_id: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )

        return self.db.scalar(statement)

    def list_documents_for_workspace(self, workspace_id: str) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def create_ingestion_job(
        self,
        workspace_id: str,
        document_id: str,
        status: JobStatus = JobStatus.QUEUED,
    ) -> IngestionJob:
        job = IngestionJob(
            workspace_id=workspace_id,
            document_id=document_id,
            status=status.value,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def add_chunk(
        self,
        workspace_id: str,
        document_id: str,
        chunk_index: int,
        text: str,
        source_page: int | None = None,
        token_count: int | None = None,
        source_metadata: dict | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            workspace_id=workspace_id,
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            source_page=source_page,
            token_count=token_count,
            source_metadata=source_metadata or {},
        )
        self.db.add(chunk)
        self.db.flush()
        return chunk

    def list_chunks_for_document(
        self,
        workspace_id: str,
        document_id: str,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(
                DocumentChunk.workspace_id == workspace_id,
                DocumentChunk.document_id == document_id,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )

        return list(self.db.scalars(statement).all())