from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AdminWorkspaceSummary(BaseModel):
    id: str
    name: str
    owner_user_id: str
    owner_email: str
    document_count: int
    failed_job_count: int
    storage_bytes: int
    plan_name: str
    created_at: datetime


class AdminIngestionJobSummary(BaseModel):
    id: str
    workspace_id: str
    document_id: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class AdminAuditEventResponse(BaseModel):
    id: str
    workspace_id: str
    actor_user_id: str | None
    event_type: str
    entity_type: str
    entity_id: str | None
    payload: dict[str, Any]
    created_at: datetime


class AdminDocumentMetadata(BaseModel):
    id: str
    workspace_id: str
    title: str
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    file_count: int
    chunk_count: int
