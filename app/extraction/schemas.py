from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractionFieldType(StrEnum):
    TEXT = "text"
    DATE = "date"
    AMOUNT = "amount"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"


class ExtractionEvidence(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    quote: str
    source_page: int | None = None
    source_start_offset: int | None = None
    source_end_offset: int | None = None


class ExtractionFieldSpec(BaseModel):
    name: str
    description: str
    field_type: ExtractionFieldType

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field name cannot be empty.")

        if not value.replace("_", "").isalnum():
            raise ValueError("Field name must use letters, numbers, and underscores only.")

        return value


class ExtractionSchema(BaseModel):
    name: str
    fields: list[ExtractionFieldSpec]

    @field_validator("fields")
    @classmethod
    def validate_unique_fields(cls, value: list[ExtractionFieldSpec]) -> list[ExtractionFieldSpec]:
        names = [field.name for field in value]

        if len(names) != len(set(names)):
            raise ValueError("Extraction schema field names must be unique.")

        return value


class ExtractedField(BaseModel):
    name: str
    value: Any
    field_type: ExtractionFieldType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: ExtractionEvidence | None
    review_flags: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    schema_name: str
    fields: list[ExtractedField]
    review_flags: list[str] = Field(default_factory=list)
