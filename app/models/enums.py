from enum import StrEnum


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class DocumentStatus(StrEnum):
    CREATED = "created"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
