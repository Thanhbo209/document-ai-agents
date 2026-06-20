class IngestionError(Exception):
    """Base error for ingestion failures."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when the uploaded file type is not supported."""


class ExtractionError(IngestionError):
    """Raised when text extraction fails."""