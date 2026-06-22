from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DocumentStatus, JobStatus, WorkspaceRole, WorkspaceStatus


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_platform_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    memberships: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    messages: Mapped[list[ConversationMessage]] = relationship(back_populates="user")
    conversation_sessions: Mapped[list[ConversationSession]] = relationship(
        back_populates="user",
    )


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(40),
        default=WorkspaceStatus.ACTIVE.value,
        nullable=False,
    )
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    members: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    subscription: Mapped[WorkspaceSubscription | None] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        uselist=False,
    )


class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_workspace_members_workspace_user", "workspace_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32),
        default=WorkspaceRole.MEMBER.value,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class WorkspaceSubscription(Base, TimestampMixin):
    __tablename__ = "workspace_subscriptions"
    __table_args__ = (Index("ix_workspace_subscriptions_workspace", "workspace_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"),
        unique=True,
        nullable=False,
    )
    plan_name: Mapped[str] = mapped_column(String(40), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="subscription")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_workspace_status", "workspace_id", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=DocumentStatus.CREATED.value,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="documents")
    files: Mapped[list[DocumentFile]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list[IngestionJob]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentFile(Base, TimestampMixin):
    __tablename__ = "document_files"
    __table_args__ = (Index("ix_document_files_workspace_document", "workspace_id", "document_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    document: Mapped[Document] = relationship(back_populates="files")


class IngestionJob(Base, TimestampMixin):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (Index("ix_ingestion_jobs_workspace_status", "workspace_id", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32),
        default=JobStatus.QUEUED.value,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship(back_populates="jobs")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
        Index("ix_document_chunks_workspace_document", "workspace_id", "document_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")
    citations: Mapped[list[Citation]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
    )


class ConversationSession(Base, TimestampMixin):
    __tablename__ = "conversation_sessions"
    __table_args__ = (
        Index("ix_conversation_sessions_workspace_updated", "workspace_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(180), default="New chat", nullable=False)

    user: Mapped[User | None] = relationship(back_populates="conversation_sessions")
    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_workspace", "workspace_id"),
        Index("ix_conversation_messages_session", "session_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversation_sessions.id"),
        nullable=True,
    )
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attached_document_ids: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    user: Mapped[User | None] = relationship(back_populates="messages")
    session: Mapped[ConversationSession | None] = relationship(back_populates="messages")
    citations: Mapped[list[Citation]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class Citation(Base, TimestampMixin):
    __tablename__ = "citations"
    __table_args__ = (
        Index("ix_citations_message", "message_id"),
        Index("ix_citations_chunk", "chunk_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_messages.id"),
        nullable=False,
    )
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    message: Mapped[ConversationMessage] = relationship(back_populates="citations")
    chunk: Mapped[DocumentChunk] = relationship(back_populates="citations")


class ReviewItem(Base, TimestampMixin):
    __tablename__ = "review_items"
    __table_args__ = (
        Index("ix_review_items_workspace_status", "workspace_id", "status"),
        Index("ix_review_items_target", "target_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)

    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)

    field_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    original_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewed_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    reviewer_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_workspace", "workspace_id"),
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class UsageEvent(Base, TimestampMixin):
    __tablename__ = "usage_events"
    __table_args__ = (
        Index("ix_usage_events_workspace_created", "workspace_id", "created_at"),
        Index("ix_usage_events_workspace_metric", "workspace_id", "metric_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)

    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    usage_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
