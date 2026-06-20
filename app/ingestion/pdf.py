from pathlib import Path

from pypdf import PdfReader

from app.ingestion.errors import ExtractionError
from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument


def extract_pdf_file(path: Path, title: str) -> NormalizedDocument:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ExtractionError(f"Could not open PDF file: {exc}") from exc

    blocks: list[ExtractedTextBlock] = []

    for page_index, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise ExtractionError(f"Could not extract text from {page_index + 1}: {exc}") from exc

        if not text.strip():
            continue

        blocks.append(
            ExtractedTextBlock(
                text=text,
                source_page=page_index + 1,
                source_start_offset=0,
                source_end_offset=len(text),
                metadata={
                    "filename": path.name,
                    "source_type": InputType.PDF.value,
                    "page_number": page_index + 1,
                },
            )
        )

    if not blocks:
        raise ExtractionError("PDF does not contain extractable text.")

    return NormalizedDocument(
        title=title,
        source_type=InputType.PDF,
        blocks=blocks,
    )
