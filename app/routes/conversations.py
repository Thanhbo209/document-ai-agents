from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import ConversationMessage
from app.db.session import get_db
from app.middleware.tenant import WorkspaceAccess, require_workspace_permission
from app.permissions.policies import WorkspacePermission
from app.repositories.conversations import ConversationRepository

router = APIRouter(tags=["chat sessions"])

query_documents_access = require_workspace_permission(WorkspacePermission.QUERY_DOCUMENTS)


class ChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=180)


class ChatSessionResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatCitationResponse(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    quote: str
    metadata: dict[str, Any]


class ChatSourceResponse(BaseModel):
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


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    updated_at: datetime
    attached_document_ids: list[str]
    citations: list[ChatCitationResponse]
    source_list: list[ChatSourceResponse]


@router.get(
    "/workspaces/{workspace_id}/chat-sessions",
    response_model=list[ChatSessionResponse],
)
def list_chat_sessions(
    workspace_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(query_documents_access),
) -> list[ChatSessionResponse]:
    repository = ConversationRepository(db)
    sessions = repository.list_sessions_for_workspace(workspace_id)
    return [
        _session_response(session=session, message_count=message_count)
        for session, message_count in sessions
        if session.workspace_id == access.workspace.id
    ]


@router.post(
    "/workspaces/{workspace_id}/chat-sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    workspace_id: str,
    request: ChatSessionCreateRequest | None = None,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(query_documents_access),
) -> ChatSessionResponse:
    repository = ConversationRepository(db)
    session = repository.create_session(
        workspace_id=workspace_id,
        user_id=access.user.id,
        title=request.title if request and request.title else "New chat",
    )
    db.commit()
    return _session_response(session=session, message_count=0)


@router.get(
    "/workspaces/{workspace_id}/chat-sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def list_chat_session_messages(
    workspace_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    access: WorkspaceAccess = Depends(query_documents_access),
) -> list[ChatMessageResponse]:
    repository = ConversationRepository(db)
    session = repository.get_session(workspace_id=workspace_id, session_id=session_id)

    if not session or session.workspace_id != access.workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session was not found in this workspace.",
        )

    messages = repository.list_messages_for_session(
        workspace_id=workspace_id,
        session_id=session_id,
    )
    return [_message_response(message) for message in messages]


def _session_response(
    session,
    message_count: int,
) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=session.id,
        workspace_id=session.workspace_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=message_count,
    )


def _message_response(message: ConversationMessage) -> ChatMessageResponse:
    citations = [
        _citation_response(rank=rank, citation=citation)
        for rank, citation in enumerate(
            sorted(message.citations, key=lambda item: item.rank),
            start=1,
        )
    ]
    sources = [
        _source_response(rank=rank, citation=citation)
        for rank, citation in enumerate(
            sorted(message.citations, key=lambda item: item.rank),
            start=1,
        )
    ]
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        updated_at=message.updated_at,
        attached_document_ids=message.attached_document_ids or [],
        citations=citations,
        source_list=sources,
    )


def _citation_response(rank, citation) -> ChatCitationResponse:
    chunk = citation.chunk
    source_id = f"S{rank}"
    return ChatCitationResponse(
        source_id=source_id,
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        workspace_id=chunk.workspace_id,
        source_page=chunk.source_page,
        source_start_offset=chunk.source_start_offset,
        source_end_offset=chunk.source_end_offset,
        quote=citation.quote or chunk.text,
        metadata=chunk.source_metadata or {},
    )


def _source_response(rank, citation) -> ChatSourceResponse:
    chunk = citation.chunk
    source_id = f"S{rank}"
    return ChatSourceResponse(
        source_id=source_id,
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        workspace_id=chunk.workspace_id,
        text=chunk.text,
        source_page=chunk.source_page,
        source_start_offset=chunk.source_start_offset,
        source_end_offset=chunk.source_end_offset,
        score=citation.relevance_score or 0.0,
        metadata=chunk.source_metadata or {},
    )
