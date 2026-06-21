from dataclasses import dataclass
from enum import StrEnum


class InputType(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    CSV = "csv"
    XLSX = "xlsx"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    REPO = "repo"
    WEB = "web"
    YOUTUBE = "youtube"


@dataclass(frozen=True)
class ExtractedTextBlock:
    text: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    metadata: dict


@dataclass(frozen=True)
class NormalizedDocument:
    title: str
    source_type: InputType
    blocks: list[ExtractedTextBlock]
