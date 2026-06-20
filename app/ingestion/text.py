from pathlib import Path

from app.ingestion.errors import ExtractionError
from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument


def extract_text_file(path: Path, title: str, source_type: InputType) -> NormalizedDocument:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ExtractionError(f"Could not read text file: {exc}") from exc

    if not text.strip():
        raise ExtractionError("File does not contain extractable text.")

    block = ExtractedTextBlock(
        text=text,
        source_page=None,
        source_start_offset=0,
        source_end_offset=len(text),
        metadata={
            "filename": path.name,
            "source_type": source_type.value,
        },
    )

    return NormalizedDocument(
        title=title,
        source_type=source_type,
        blocks=[block],
    )
