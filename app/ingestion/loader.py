from pathlib import Path

from app.core.config import get_settings
from app.ingestion.errors import ExtractionError, UnsupportedFileTypeError
from app.ingestion.ocr import OcrEngine
from app.ingestion.office import extract_docx_file, extract_pptx_file
from app.ingestion.pdf import extract_image_file, extract_pdf_file
from app.ingestion.tables import extract_csv_file, extract_xlsx_file
from app.ingestion.text import extract_text_file
from app.ingestion.transcribe import Transcriber, WhisperTranscriber
from app.ingestion.types import InputType, NormalizedDocument
from app.media.ffmpeg import AudioExtractor, FFmpegAudioExtractor
from app.storage.artifacts import ArtifactStorage
from app.workers.media_worker import MediaWorker

_EXTENSION_TO_INPUT_TYPE = {
    ".txt": InputType.TEXT,
    ".md": InputType.MARKDOWN,
    ".markdown": InputType.MARKDOWN,
    ".pdf": InputType.PDF,
    ".docx": InputType.DOCX,
    ".pptx": InputType.PPTX,
    ".csv": InputType.CSV,
    ".xlsx": InputType.XLSX,
    ".png": InputType.IMAGE,
    ".jpg": InputType.IMAGE,
    ".jpeg": InputType.IMAGE,
    ".tiff": InputType.IMAGE,
    ".tif": InputType.IMAGE,
    ".bmp": InputType.IMAGE,
    ".mp3": InputType.AUDIO,
    ".wav": InputType.AUDIO,
    ".m4a": InputType.AUDIO,
    ".flac": InputType.AUDIO,
    ".ogg": InputType.AUDIO,
    ".mp4": InputType.VIDEO,
    ".mov": InputType.VIDEO,
    ".mkv": InputType.VIDEO,
    ".webm": InputType.VIDEO,
}

_SUPPORTED_EXTENSIONS = ", ".join(sorted(_EXTENSION_TO_INPUT_TYPE))


def detect_input_type(filename: str, content_type: str | None = None) -> InputType:
    extension = Path(filename).suffix.lower()

    if extension in _EXTENSION_TO_INPUT_TYPE:
        return _EXTENSION_TO_INPUT_TYPE[extension]

    raise UnsupportedFileTypeError(
        f"Unsupported file type for '{filename}'. Supported types: {_SUPPORTED_EXTENSIONS}"
    )


def load_document(
    path: Path,
    input_type: InputType,
    title: str,
    workspace_id: str | None = None,
    document_id: str | None = None,
    artifact_storage: ArtifactStorage | None = None,
    ocr_engine: OcrEngine | None = None,
    audio_extractor: AudioExtractor | None = None,
    transcriber: Transcriber | None = None,
) -> NormalizedDocument:
    if input_type in {InputType.TEXT, InputType.MARKDOWN}:
        return extract_text_file(path=path, title=title, source_type=input_type)

    if input_type == InputType.PDF:
        return extract_pdf_file(
            path=path,
            title=title,
            workspace_id=workspace_id,
            document_id=document_id,
            artifact_storage=artifact_storage,
            ocr_engine=ocr_engine,
        )

    if input_type == InputType.DOCX:
        return extract_docx_file(path=path, title=title)

    if input_type == InputType.PPTX:
        return extract_pptx_file(path=path, title=title)

    if input_type == InputType.CSV:
        return extract_csv_file(path=path, title=title)

    if input_type == InputType.XLSX:
        return extract_xlsx_file(path=path, title=title)

    if input_type == InputType.IMAGE:
        return extract_image_file(
            path=path,
            title=title,
            workspace_id=workspace_id,
            document_id=document_id,
            artifact_storage=artifact_storage,
            ocr_engine=ocr_engine,
        )

    if input_type in {InputType.AUDIO, InputType.VIDEO}:
        storage = artifact_storage or ArtifactStorage(get_settings().artifact_dir)
        worker = MediaWorker(
            artifact_storage=storage,
            audio_extractor=audio_extractor or FFmpegAudioExtractor(),
            transcriber=transcriber or WhisperTranscriber(get_settings().whisper_model_name),
        )
        try:
            blocks = worker.process_media(
                workspace_id=workspace_id or "standalone",
                document_id=document_id or path.stem,
                input_path=path,
            )
        except Exception as exc:
            raise ExtractionError(str(exc)) from exc

        if not blocks:
            raise ExtractionError("Media transcription did not produce text.")

        return NormalizedDocument(
            title=title,
            source_type=input_type,
            blocks=blocks,
        )

    raise UnsupportedFileTypeError(f"Unsupported input type: {input_type}")
