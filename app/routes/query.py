import json
from collections.abc import Generator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.answers.generator import GroundedAnswerGenerationError, GroundedAnswerGenerator
from app.answers.types import AnswerCitation, AnswerSource, GroundedAnswer
from app.db.models import Document
from app.db.session import get_db
from app.indexing.indexer import DocumentIndexer
from app.llm.client import LocalGroundedLLMClient
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.models.enums import MessageRole
from app.permissions.policies import WorkspacePermission
from app.repositories.conversations import ConversationRepository
from app.retrieval.filters import RetrievalFilters
from app.retrieval.reranker import KeywordOverlapReranker
from app.retrieval.retriever import RetrievalRequest, Retriever
from app.retrieval.types import RetrievedChunk
from app.services.vector_runtime import get_runtime_embedder, get_runtime_vector_store

router = APIRouter(tags=["query"])

access: WorkspaceAccess = (
    Depends(require_workspace_permission(WorkspacePermission.QUERY_DOCUMENTS)),
)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    document_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class QueryCitationResponse(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    quote: str
    metadata: dict[str, Any]


class QuerySourceResponse(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    score: float
    metadata: dict[str, Any]


class QueryResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    message: str
    citations: list[QueryCitationResponse]
    source_list: list[QuerySourceResponse]
    confidence: float
    review_flags: list[str]
    model_name: str
    prompt_id: str


@router.post(
    "/workspaces/{workspace_id}/query",
    response_model=QueryResponse,
)
def query_workspace(
    workspace_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
) -> QueryResponse:
    return _run_query(workspace_id=workspace_id, request=request, db=db, user_id=access.user.id)


@router.post("/workspaces/{workspace_id}/query/stream")
def stream_query_workspace(
    workspace_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    response = _run_query(
        workspace_id=workspace_id,
        request=request,
        db=db,
    )

    return StreamingResponse(
        _stream_query_response(response),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _run_query(
    workspace_id: str,
    request: QueryRequest,
    db: Session,
    user_id: str,
) -> QueryResponse:

    document_ids = _resolve_document_ids(
        db=db,
        workspace_id=workspace_id,
        requested_document_ids=request.document_ids,
    )

    _index_documents_for_query(
        db=db,
        workspace_id=workspace_id,
        document_ids=document_ids,
    )

    retrieved_chunks = _retrieve_chunks(
        workspace_id=workspace_id,
        query=request.query,
        document_ids=request.document_ids,
        top_k=request.top_k,
    )

    try:
        answer = GroundedAnswerGenerator(LocalGroundedLLMClient()).generate(
            query=request.query,
            retrieved_chunks=retrieved_chunks,
        )
    except GroundedAnswerGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Grounded answer validation failed.",
                "error": str(exc),
            },
        ) from exc

    user_message_id, assistant_message_id = _persist_conversation(
        db=db,
        workspace_id=workspace_id,
        user_id=user_id,
        query=request.query,
        answer=answer,
    )

    db.commit()

    return _query_response_from_answer(
        user_message_id=user_message_id,
        assistant_message_id=assistant_message_id,
        answer=answer,
    )


def _resolve_document_ids(
    db: Session,
    workspace_id: str,
    requested_document_ids: list[str] | None,
) -> list[str]:
    statement = select(Document.id).where(Document.workspace_id == workspace_id)

    if requested_document_ids:
        statement = statement.where(Document.id.in_(requested_document_ids))

    document_ids = list(db.scalars(statement).all())

    if requested_document_ids and len(document_ids) != len(set(requested_document_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more selected documents were not found in this workspace.",
        )

    return document_ids


def _index_documents_for_query(
    db: Session,
    workspace_id: str,
    document_ids: list[str],
) -> None:
    embedder = get_runtime_embedder()
    vector_store = get_runtime_vector_store()

    indexer = DocumentIndexer(
        db=db,
        embedder=embedder,
        vector_store=vector_store,
    )

    for document_id in document_ids:
        indexer.index_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )


def _retrieve_chunks(
    workspace_id: str,
    query: str,
    document_ids: list[str] | None,
    top_k: int,
) -> list[RetrievedChunk]:
    filters = RetrievalFilters(document_ids=document_ids) if document_ids else None

    retriever = Retriever(
        embedder=get_runtime_embedder(),
        vector_store=get_runtime_vector_store(),
        reranker=KeywordOverlapReranker(),
    )

    return retriever.retrieve(
        RetrievalRequest(
            workspace_id=workspace_id,
            query=query,
            top_k=top_k,
            filters=filters,
        )
    )


def _persist_conversation(
    db: Session,
    workspace_id: str,
    user_id: str,
    query: str,
    answer: GroundedAnswer,
) -> tuple[str, str]:
    conversation_repo = ConversationRepository(db)

    user_message = conversation_repo.create_message(
        workspace_id=workspace_id,
        role=MessageRole.USER,
        content=query,
        user_id=user_id,
    )
    assistant_message = conversation_repo.create_message(
        workspace_id=workspace_id,
        role=MessageRole.ASSISTANT,
        content=answer.message,
    )

    source_score_by_id = {source.source_id: source.score for source in answer.source_list}

    for rank, citation in enumerate(answer.citations, start=1):
        conversation_repo.create_citation(
            message_id=assistant_message.id,
            chunk_id=citation.chunk_id,
            rank=rank,
            relevance_score=source_score_by_id.get(citation.source_id),
            quote=citation.quote,
        )

    return user_message.id, assistant_message.id


def _query_response_from_answer(
    user_message_id: str,
    assistant_message_id: str,
    answer: GroundedAnswer,
) -> QueryResponse:
    return QueryResponse(
        user_message_id=user_message_id,
        assistant_message_id=assistant_message_id,
        message=answer.message,
        citations=[_citation_response(citation) for citation in answer.citations],
        source_list=[_source_response(source) for source in answer.source_list],
        confidence=answer.confidence,
        review_flags=answer.review_flags,
        model_name=answer.model_name,
        prompt_id=answer.prompt_id,
    )


def _citation_response(citation: AnswerCitation) -> QueryCitationResponse:
    return QueryCitationResponse(
        source_id=citation.source_id,
        chunk_id=citation.chunk_id,
        document_id=citation.document_id,
        workspace_id=citation.workspace_id,
        source_page=citation.source_page,
        source_start_offset=citation.source_start_offset,
        source_end_offset=citation.source_end_offset,
        quote=citation.quote,
        metadata=citation.metadata,
    )


def _source_response(source: AnswerSource) -> QuerySourceResponse:
    return QuerySourceResponse(
        source_id=source.source_id,
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        workspace_id=source.workspace_id,
        text=source.text,
        source_page=source.source_page,
        source_start_offset=source.source_start_offset,
        source_end_offset=source.source_end_offset,
        score=source.score,
        metadata=source.metadata,
    )


def _stream_query_response(
    response: QueryResponse,
) -> Generator[str]:
    yield _sse_event(
        event="start",
        data={
            "assistant_message_id": response.assistant_message_id,
        },
    )

    for token in response.message.split(" "):
        yield _sse_event(
            event="token",
            data={
                "text": f"{token} ",
            },
        )

    yield _sse_event(
        event="final",
        data=response.model_dump(mode="json"),
    )


def _sse_event(
    event: str,
    data: dict[str, Any],
) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
