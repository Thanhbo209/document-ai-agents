from pathlib import Path

from app.ingestion.errors import UnsupportedFileTypeError
from app.ingestion.office import extract_docx_file, extract_pptx_file
from app.ingestion.pdf import extract_pdf_file
from app.ingestion.tables import extract_csv_file, extract_xlsx_file
from app.ingestion.text import extract_text_file
from app.ingestion.types import InputType, NormalizedDocument

_EXTENSION_TO_INPUT_TYPE = {
    ".txt": InputType.TEXT,
    ".md": InputType.MARKDOWN,
    ".markdown": InputType.MARKDOWN,
    ".pdf": InputType.PDF,
    ".docx": InputType.DOCX,
    ".pptx": InputType.PPTX,
    ".csv": InputType.CSV,
    ".xlsx": InputType.XLSX,
}

_SUPPORTED_EXTENSIONS = ", ".join(sorted(_EXTENSION_TO_INPUT_TYPE))


def detect_input_type(filename: str, content_type: str | None = None) -> InputType:
    extension = Path(filename).suffix.lower()

    if extension in _EXTENSION_TO_INPUT_TYPE:
        return _EXTENSION_TO_INPUT_TYPE[extension]

    raise UnsupportedFileTypeError(
        f"Unsupported file type for '{filename}'. Supported types: {_SUPPORTED_EXTENSIONS}"
    )


def load_document(path: Path, input_type: InputType, title: str) -> NormalizedDocument:
    if input_type in {InputType.TEXT, InputType.MARKDOWN}:
        return extract_text_file(path=path, title=title, source_type=input_type)

    if input_type == InputType.PDF:
        return extract_pdf_file(path=path, title=title)

    if input_type == InputType.DOCX:
        return extract_docx_file(path=path, title=title)

    if input_type == InputType.PPTX:
        return extract_pptx_file(path=path, title=title)

    if input_type == InputType.CSV:
        return extract_csv_file(path=path, title=title)

    if input_type == InputType.XLSX:
        return extract_xlsx_file(path=path, title=title)

    raise UnsupportedFileTypeError(f"Unsupported input type: {input_type}")
