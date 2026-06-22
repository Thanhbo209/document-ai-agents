from pathlib import Path

from pypdf import PdfReader

from app.core.config import get_settings
from app.ingestion.errors import ExtractionError
from app.ingestion.ocr import OcrEngine, OcrEngineUnavailableError, OcrError, TesseractOcrEngine
from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument
from app.storage.artifacts import ArtifactStorage
from app.workers.ocr_worker import OcrWorker

MIN_EXTRACTED_TEXT_CHARS_BEFORE_OCR = 50


def extract_pdf_file(
    path: Path,
    title: str,
    workspace_id: str | None = None,
    document_id: str | None = None,
    artifact_storage: ArtifactStorage | None = None,
    ocr_engine: OcrEngine | None = None,
) -> NormalizedDocument:
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
                    "ocr": False,
                },
            )
        )

    total_text_chars = sum(len(block.text.strip()) for block in blocks)
    needs_ocr = total_text_chars < MIN_EXTRACTED_TEXT_CHARS_BEFORE_OCR
    requires_ocr = not blocks

    if needs_ocr and get_settings().ocr_enabled:
        ocr_blocks = _run_pdf_ocr_fallback(
            path=path,
            workspace_id=workspace_id,
            document_id=document_id,
            artifact_storage=artifact_storage,
            ocr_engine=ocr_engine,
            required=requires_ocr,
        )

        if ocr_blocks:
            return NormalizedDocument(
                title=title,
                source_type=InputType.PDF,
                blocks=ocr_blocks,
            )

    if requires_ocr:
        if not get_settings().ocr_enabled:
            raise ExtractionError("PDF does not contain extractable text and OCR is disabled.")

        raise ExtractionError("PDF does not contain extractable text.")

    return NormalizedDocument(
        title=title,
        source_type=InputType.PDF,
        blocks=blocks,
    )


def extract_image_file(
    path: Path,
    title: str,
    workspace_id: str | None = None,
    document_id: str | None = None,
    artifact_storage: ArtifactStorage | None = None,
    ocr_engine: OcrEngine | None = None,
) -> NormalizedDocument:
    settings = get_settings()

    if not settings.ocr_enabled:
        raise ExtractionError("OCR is disabled. Image ingestion requires OCR.")

    storage = artifact_storage or ArtifactStorage(settings.artifact_dir)
    engine = ocr_engine or TesseractOcrEngine(
        settings.ocr_low_confidence_threshold,
        tesseract_cmd=settings.ocr_tesseract_cmd,
    )

    try:
        blocks = OcrWorker(
            artifact_storage=storage,
            ocr_engine=engine,
        ).process_image(
            workspace_id=workspace_id or "standalone",
            document_id=document_id or path.stem,
            image_path=path,
        )
    except OcrEngineUnavailableError as exc:
        raise ExtractionError(str(exc)) from exc
    except OcrError as exc:
        raise ExtractionError(str(exc)) from exc

    if not blocks:
        raise ExtractionError("OCR did not extract text from image.")

    return NormalizedDocument(
        title=title,
        source_type=InputType.IMAGE,
        blocks=blocks,
    )


def _run_pdf_ocr_fallback(
    path: Path,
    workspace_id: str | None,
    document_id: str | None,
    artifact_storage: ArtifactStorage | None,
    ocr_engine: OcrEngine | None,
    required: bool,
) -> list[ExtractedTextBlock]:
    settings = get_settings()
    storage = artifact_storage or ArtifactStorage(settings.artifact_dir)
    engine = ocr_engine or TesseractOcrEngine(
        settings.ocr_low_confidence_threshold,
        tesseract_cmd=settings.ocr_tesseract_cmd,
    )

    try:
        return OcrWorker(
            artifact_storage=storage,
            ocr_engine=engine,
        ).process_scanned_pdf(
            workspace_id=workspace_id or "standalone",
            document_id=document_id or path.stem,
            pdf_path=path,
        )
    except OcrEngineUnavailableError as exc:
        if required:
            raise ExtractionError(str(exc)) from exc

        return []
    except OcrError as exc:
        if required:
            raise ExtractionError(str(exc)) from exc

        return []
