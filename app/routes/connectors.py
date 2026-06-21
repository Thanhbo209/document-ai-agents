from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit.events import AuditEventRepository
from app.billing.subscriptions import WorkspaceSubscriptionRepository
from app.billing.usage import UsageRepository
from app.core.config import get_settings
from app.db.models import IngestionJob
from app.db.session import get_db
from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument
from app.ingestion.web import (
    UrlFetchError,
    UrlLibWebPageFetcher,
    UrlNotAllowedError,
    UrlSafetyError,
    WebFetchPolicy,
    WebPageFetcher,
    extract_web_blocks,
)
from app.ingestion.youtube import (
    YouTubeTranscriptApiClient,
    YouTubeTranscriptClient,
    YouTubeTranscriptError,
    extract_youtube_blocks,
    extract_youtube_video_id,
)
from app.limits.policies import LimitExceededError
from app.limits.service import QuotaService, quota_error_response
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.models.chunk import ChunkingConfig
from app.models.enums import DocumentStatus, JobStatus
from app.permissions.policies import WorkspacePermission
from app.processing.chunker import chunk_document
from app.repositories.documents import DocumentRepository

router = APIRouter(tags=["connectors"])

ingest_connectors_access = require_workspace_permission(WorkspacePermission.UPLOAD_DOCUMENTS)


class ConnectorIngestRequest(BaseModel):
    source_type: Literal["web", "youtube"]
    url: str


class ConnectorIngestResponse(BaseModel):
    document_id: str
    job_id: str
    status: str
    chunks_created: int


def get_web_fetch_policy() -> WebFetchPolicy:
    settings = get_settings()
    return WebFetchPolicy(
        allowed_domains=tuple(settings.connector_web_allowed_domains),
        blocked_domains=tuple(settings.connector_web_blocked_domains),
        max_response_bytes=settings.connector_web_max_response_bytes,
        timeout_seconds=settings.connector_web_timeout_seconds,
    )


def get_web_page_fetcher() -> WebPageFetcher:
    return UrlLibWebPageFetcher()


def get_youtube_transcript_client() -> YouTubeTranscriptClient:
    return YouTubeTranscriptApiClient()


@router.post(
    "/workspaces/{workspace_id}/connectors/ingest",
    response_model=ConnectorIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_connector(
    workspace_id: str,
    request: ConnectorIngestRequest,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(ingest_connectors_access),
    web_policy: WebFetchPolicy = Depends(get_web_fetch_policy),
    web_fetcher: WebPageFetcher = Depends(get_web_page_fetcher),
    youtube_client: YouTubeTranscriptClient = Depends(get_youtube_transcript_client),
) -> ConnectorIngestResponse:
    usage_repo = UsageRepository(db)
    quota_service = QuotaService(
        usage_repo=usage_repo,
        subscription_repo=WorkspaceSubscriptionRepository(db),
    )

    try:
        quota_service.assert_can_upload(
            workspace_id=workspace_id,
            file_size_bytes=0,
        )
    except LimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota_error_response(exc),
        ) from exc

    document_repo = DocumentRepository(db)
    title = _initial_title(request)
    source_type = InputType(request.source_type)
    document = document_repo.create_document(
        workspace_id=workspace_id,
        title=title,
        source_type=source_type.value,
        status=DocumentStatus.PROCESSING,
    )
    job = document_repo.create_ingestion_job(
        workspace_id=workspace_id,
        document_id=document.id,
        status=JobStatus.PROCESSING,
    )
    db.commit()

    try:
        blocks = _extract_connector_blocks(
            request=request,
            web_policy=web_policy,
            web_fetcher=web_fetcher,
            youtube_client=youtube_client,
        )

        if not blocks:
            raise ValueError("Connector did not produce text.")

        document.title = _title_from_blocks(blocks, fallback=title)
        chunks = _store_connector_chunks(
            db=db,
            document_repo=document_repo,
            workspace_id=workspace_id,
            document_id=document.id,
            document_title=document.title,
            source_type=source_type,
            blocks=blocks,
        )

        document_repo.update_document_status(document, DocumentStatus.INDEXED)
        document_repo.update_ingestion_job_status(job, JobStatus.SUCCEEDED)
        usage_repo.record_usage(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
            metric_name="document.count",
            quantity=1,
            unit="document",
            source_type="document",
            source_id=document.id,
        )
        usage_repo.record_usage(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
            metric_name="chunk.count",
            quantity=len(chunks),
            unit="chunk",
            source_type="document",
            source_id=document.id,
        )
        usage_repo.record_usage(
            workspace_id=workspace_id,
            actor_user_id=access.user.id,
            metric_name="chunk.tokens",
            quantity=sum(chunk.token_count for chunk in chunks),
            unit="token",
            source_type="document",
            source_id=document.id,
        )
        AuditEventRepository(db).record_event(
            workspace_id=workspace_id,
            event_type="ingestion.connector_ingested",
            entity_type="document",
            entity_id=document.id,
            actor_user_id=access.user.id,
            payload={
                "source_type": request.source_type,
                "url": request.url,
                "chunk_count": len(chunks),
            },
        )
        db.commit()

        return ConnectorIngestResponse(
            document_id=document.id,
            job_id=job.id,
            status=job.status,
            chunks_created=len(chunks),
        )

    except (UrlNotAllowedError, UrlSafetyError, YouTubeTranscriptError) as exc:
        db.rollback()
        _mark_connector_ingestion_failed(
            db=db,
            document_repo=document_repo,
            workspace_id=workspace_id,
            document_id=document.id,
            job_id=job.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (UrlFetchError, ValueError) as exc:
        db.rollback()
        _mark_connector_ingestion_failed(
            db=db,
            document_repo=document_repo,
            workspace_id=workspace_id,
            document_id=document.id,
            job_id=job.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Connector ingestion failed.",
                "job_id": job.id,
                "error": str(exc),
            },
        ) from exc


def _extract_connector_blocks(
    request: ConnectorIngestRequest,
    web_policy: WebFetchPolicy,
    web_fetcher: WebPageFetcher,
    youtube_client: YouTubeTranscriptClient,
) -> list[ExtractedTextBlock]:
    if request.source_type == "web":
        return extract_web_blocks(
            url=request.url,
            policy=web_policy,
            fetcher=web_fetcher,
        )

    return extract_youtube_blocks(
        url_or_id=request.url,
        client=youtube_client,
    )


def _store_connector_chunks(
    db: Session,
    document_repo: DocumentRepository,
    workspace_id: str,
    document_id: str,
    document_title: str,
    source_type: InputType,
    blocks: list[ExtractedTextBlock],
):
    settings = get_settings()
    chunks = chunk_document(
        document=NormalizedDocument(
            title=document_title,
            source_type=source_type,
            blocks=blocks,
        ),
        config=ChunkingConfig(
            max_tokens=settings.chunk_max_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        ),
    )

    for index, chunk in enumerate(chunks):
        document_repo.add_chunk(
            workspace_id=workspace_id,
            document_id=document_id,
            chunk_index=index,
            text=chunk.text,
            source_page=chunk.source_page,
            source_start_offset=chunk.source_start_offset,
            source_end_offset=chunk.source_end_offset,
            token_count=chunk.token_count,
            source_metadata=chunk.metadata,
        )

    db.flush()
    return chunks


def _mark_connector_ingestion_failed(
    db: Session,
    document_repo: DocumentRepository,
    workspace_id: str,
    document_id: str,
    job_id: str,
    error_message: str,
) -> None:
    failed_job = db.get(IngestionJob, job_id)
    if failed_job is not None:
        document_repo.update_ingestion_job_status(
            failed_job,
            JobStatus.FAILED,
            error_message=error_message,
        )

    failed_document = document_repo.get_document_for_workspace(
        document_id=document_id,
        workspace_id=workspace_id,
    )
    if failed_document is not None:
        document_repo.update_document_status(failed_document, DocumentStatus.FAILED)

    db.commit()


def _initial_title(request: ConnectorIngestRequest) -> str:
    if request.source_type == "youtube":
        try:
            return f"YouTube {extract_youtube_video_id(request.url)}"
        except YouTubeTranscriptError:
            return "YouTube transcript"

    return request.url.strip()[:255] or "Web page"


def _title_from_blocks(blocks: list[ExtractedTextBlock], fallback: str) -> str:
    metadata = blocks[0].metadata if blocks else {}
    title = metadata.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()[:255]

    return fallback[:255]
