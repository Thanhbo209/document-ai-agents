import pytest

from app.ingestion.errors import UnsupportedFileTypeError
from app.ingestion.loader import detect_input_type
from app.ingestion.types import InputType


def test_detect_input_type_for_supported_files() -> None:
    assert detect_input_type("notes.txt") == InputType.TEXT
    assert detect_input_type("README.md") == InputType.MARKDOWN
    assert detect_input_type("paper.pdf") == InputType.PDF


def test_detect_input_type_rejects_unsupported_file() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        detect_input_type("malware.exe")
