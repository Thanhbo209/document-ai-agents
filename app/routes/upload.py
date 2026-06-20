from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import IngestionJob, Workspace
from app.db.session import get_db
from app.ingestion.errors import ExtractionError, UnsupportedFileTypeError
from app.ingestion.loader import detect_input_type, load_document
from app.models.chunk import ChunkingConfig
from app.models.enums import DocumentStatus, JobStatus
from app.processing.chunker import chunk_document
from app.repositories.documents import DocumentRepository
from app.storage.local import LocalFileStorage

router = APIRouter(tags=["uploads"])


class UploadDocumentResponse(BaseModel):
    document_id: str
    file_id: str
    job_id: str
    status: str
    chunks_created: int


def get_file_storage() -> LocalFileStorage:
    settings = get_settings()
    return LocalFileStorage(settings.upload_dir)


@router.post(
    "/workspaces/{workspace_id}/documents/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: LocalFileStorage = Depends(get_file_storage),
) -> UploadDocumentResponse:
    settings = get_settings()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    try:
        input_type = detect_input_type(
            filename=file.filename,
            content_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size.",
        )

    document_repo = DocumentRepository(db)

    document = document_repo.create_document(
        workspace_id=workspace_id,
        title=Path(file.filename).stem,
        source_type=input_type.value,
        status=DocumentStatus.PROCESSING,
    )
    job = document_repo.create_ingestion_job(
        workspace_id=workspace_id,
        document_id=document.id,
        status=JobStatus.PROCESSING,
    )

    stored_file = storage.save_bytes(
        workspace_id=workspace_id,
        document_id=document.id,
        filename=file.filename,
        content=content,
    )

    document_file = document_repo.create_document_file(
        workspace_id=workspace_id,
        document_id=document.id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=stored_file.size_bytes,
        storage_key=stored_file.storage_key,
        checksum_sha256=stored_file.checksum_sha256,
    )

    db.commit()

    try:
        normalized_document = load_document(
            path=stored_file.path,
            input_type=input_type,
            title=document.title,
        )

        chunking_config = ChunkingConfig(
            max_tokens=settings.chunk_max_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        chunks = chunk_document(
            document=normalized_document,
            config=chunking_config,
        )

        for index, chunk in enumerate(chunks):
            document_repo.add_chunk(
                workspace_id=workspace_id,
                document_id=document.id,
                chunk_index=index,
                text=chunk.text,
                source_page=chunk.source_page,
                source_start_offset=chunk.source_start_offset,
                source_end_offset=chunk.source_end_offset,
                token_count=chunk.token_count,
                source_metadata=chunk.metadata,
            )

        document_repo.update_document_status(document, DocumentStatus.INDEXED)
        document_repo.update_ingestion_job_status(job, JobStatus.SUCCEEDED)
        db.commit()

        return UploadDocumentResponse(
            document_id=document.id,
            file_id=document_file.id,
            job_id=job.id,
            status=job.status,
            chunks_created=len(chunks),
        )

    except ExtractionError as exc:
        db.rollback()

        failed_job = db.get(IngestionJob, job.id)
        if failed_job is not None:
            document_repo.update_ingestion_job_status(
                failed_job,
                JobStatus.FAILED,
                error_message=str(exc),
            )

        failed_document = document_repo.get_document_for_workspace(
            document_id=document.id,
            workspace_id=workspace_id,
        )
        if failed_document is not None:
            document_repo.update_document_status(failed_document, DocumentStatus.FAILED)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Document ingestion failed.",
                "job_id": job.id,
                "error": str(exc),
            },
        ) from exc
