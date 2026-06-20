from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, DocumentFile, IngestionJob, Workspace
from app.db.session import get_db

router = APIRouter(tags=["documents"])


class DocumentFileResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    checksum_sha256: str | None


class LatestJobResponse(BaseModel):
    id: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentListItemResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    files: list[DocumentFileResponse]
    latest_job: LatestJobResponse | None
    chunk_count: int


class DocumentListResponse(BaseModel):
    workspace_id: str
    total: int
    documents: list[DocumentListItemResponse]


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentListResponse,
)
def list_workspace_documents(
    workspace_id: str,
    query: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    statement = select(Document).where(Document.workspace_id == workspace_id)

    if query:
        search_pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Document.title.ilike(search_pattern),
                Document.source_type.ilike(search_pattern),
            )
        )

    if status_filter:
        statement = statement.where(Document.status == status_filter)

    statement = statement.order_by(Document.created_at.desc())

    documents = list(db.scalars(statement).all())

    items = [
        _document_to_response(
            db=db,
            document=document,
        )
        for document in documents
    ]

    return DocumentListResponse(
        workspace_id=workspace_id,
        total=len(items),
        documents=items,
    )


def _document_to_response(
    db: Session,
    document: Document,
) -> DocumentListItemResponse:
    files = list(
        db.scalars(
            select(DocumentFile)
            .where(
                DocumentFile.workspace_id == document.workspace_id,
                DocumentFile.document_id == document.id,
            )
            .order_by(DocumentFile.created_at.asc())
        ).all()
    )

    latest_job = db.scalar(
        select(IngestionJob)
        .where(
            IngestionJob.workspace_id == document.workspace_id,
            IngestionJob.document_id == document.id,
        )
        .order_by(IngestionJob.created_at.desc())
        .limit(1)
    )

    chunk_count = db.scalar(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.workspace_id == document.workspace_id,
            DocumentChunk.document_id == document.id,
        )
    )

    return DocumentListItemResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        title=document.title,
        source_type=document.source_type,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
        files=[
            DocumentFileResponse(
                id=file.id,
                filename=file.filename,
                content_type=file.content_type,
                size_bytes=file.size_bytes,
                storage_key=file.storage_key,
                checksum_sha256=file.checksum_sha256,
            )
            for file in files
        ],
        latest_job=(
            LatestJobResponse(
                id=latest_job.id,
                status=latest_job.status,
                error_message=latest_job.error_message,
                created_at=latest_job.created_at,
                updated_at=latest_job.updated_at,
            )
            if latest_job is not None
            else None
        ),
        chunk_count=chunk_count or 0,
    )
