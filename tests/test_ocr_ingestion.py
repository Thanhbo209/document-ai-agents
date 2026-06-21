from pathlib import Path

import pytest

from app.ingestion.errors import ExtractionError
from app.ingestion.loader import load_document
from app.ingestion.ocr import (
    OcrBoundingBox,
    OcrEngineUnavailableError,
    OcrLine,
    OcrPageResult,
    OcrToken,
    TesseractOcrEngine,
    ocr_results_to_text_blocks,
)
from app.ingestion.pdf import extract_pdf_file
from app.ingestion.types import InputType
from app.storage.artifacts import ArtifactStorage


class FakeOcrEngine:
    def __init__(
        self,
        text: str = "Scanned refund policy allows cancellation within 14 days.",
        confidence: float = 0.92,
    ) -> None:
        self.text = text
        self.confidence = confidence
        self.calls: list[tuple[Path, int]] = []

    def extract_page(self, image_path: Path, page_number: int) -> OcrPageResult:
        self.calls.append((image_path, page_number))
        bbox = OcrBoundingBox(x=10, y=20, width=260, height=24)
        token = OcrToken(
            text=self.text,
            confidence=self.confidence,
            bbox=bbox,
        )
        line = OcrLine(
            text=self.text,
            confidence=self.confidence,
            bbox=bbox,
            tokens=[token],
        )

        return OcrPageResult(
            page_number=page_number,
            text=self.text,
            confidence=self.confidence,
            lines=[line],
            low_confidence=self.confidence < 0.65,
            image_path=str(image_path),
        )


def test_ocr_result_converts_to_extracted_text_block() -> None:
    result = FakeOcrEngine().extract_page(Path("page-002.png"), page_number=2)

    blocks = ocr_results_to_text_blocks([result], source_type="ocr_pdf")

    assert len(blocks) == 1
    assert "OCR Page 2" in blocks[0].text
    assert "Scanned refund policy" in blocks[0].text
    assert blocks[0].source_page == 2
    assert blocks[0].metadata["ocr"] is True
    assert blocks[0].metadata["source_type"] == "ocr_pdf"
    assert blocks[0].metadata["ocr_confidence"] == 0.92
    assert blocks[0].metadata["page_number"] == 2
    assert blocks[0].metadata["bounding_boxes"][0]["bbox"] == {
        "x": 10,
        "y": 20,
        "width": 260,
        "height": 24,
    }


def test_low_confidence_ocr_is_flagged() -> None:
    result = FakeOcrEngine(confidence=0.4).extract_page(Path("page-001.png"), page_number=1)

    blocks = ocr_results_to_text_blocks([result], source_type="ocr_pdf")

    assert blocks[0].metadata["ocr_confidence"] == 0.4
    assert blocks[0].metadata["low_confidence"] is True


def test_scanned_pdf_falls_back_to_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned.pdf"
    create_scanned_pdf(pdf_path, tmp_path / "scan.png")
    fake_engine = FakeOcrEngine()

    document = extract_pdf_file(
        path=pdf_path,
        title="scanned",
        workspace_id="workspace-ocr",
        document_id="document-ocr",
        artifact_storage=ArtifactStorage(tmp_path / "artifacts"),
        ocr_engine=fake_engine,
    )

    assert document.source_type == InputType.PDF
    assert fake_engine.calls
    assert len(document.blocks) == 1
    assert document.blocks[0].metadata["source_type"] == "ocr_pdf"
    assert document.blocks[0].metadata["ocr_confidence"] == 0.92
    assert "Scanned refund policy" in document.blocks[0].text


def test_text_pdf_does_not_call_ocr_when_text_is_extractable(tmp_path: Path) -> None:
    pdf_path = tmp_path / "text.pdf"
    pdf_path.write_bytes(
        build_minimal_pdf(
            "This searchable PDF contains enough embedded text to avoid OCR fallback entirely."
        )
    )
    fake_engine = FakeOcrEngine()

    document = extract_pdf_file(
        path=pdf_path,
        title="text",
        artifact_storage=ArtifactStorage(tmp_path / "artifacts"),
        ocr_engine=fake_engine,
    )

    assert document.source_type == InputType.PDF
    assert fake_engine.calls == []
    assert document.blocks[0].metadata["ocr"] is False
    assert "searchable PDF" in document.blocks[0].text


def test_image_document_routes_to_ocr(tmp_path: Path) -> None:
    image_path = tmp_path / "scan.png"
    create_text_image(image_path)
    fake_engine = FakeOcrEngine()

    document = load_document(
        path=image_path,
        input_type=InputType.IMAGE,
        title="scan",
        workspace_id="workspace-image",
        document_id="document-image",
        artifact_storage=ArtifactStorage(tmp_path / "artifacts"),
        ocr_engine=fake_engine,
    )

    assert document.source_type == InputType.IMAGE
    assert fake_engine.calls
    assert document.blocks[0].metadata["source_type"] == "image"
    assert document.blocks[0].metadata["ocr"] is True


def test_ocr_engine_unavailable_error_is_readable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pytesseract

    image_path = tmp_path / "scan.png"
    create_text_image(image_path)

    def raise_missing_engine(*args, **kwargs):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "image_to_data", raise_missing_engine)

    with pytest.raises(OcrEngineUnavailableError, match="Install Tesseract"):
        TesseractOcrEngine().extract_page(image_path, page_number=1)


def test_scanned_pdf_without_ocr_engine_fails_clearly(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned.pdf"
    create_scanned_pdf(pdf_path, tmp_path / "scan.png")

    class MissingOcrEngine:
        def extract_page(self, image_path: Path, page_number: int) -> OcrPageResult:
            raise OcrEngineUnavailableError()

    with pytest.raises(ExtractionError, match="OCR engine unavailable"):
        extract_pdf_file(
            path=pdf_path,
            title="scanned",
            artifact_storage=ArtifactStorage(tmp_path / "artifacts"),
            ocr_engine=MissingOcrEngine(),
        )


def create_text_image(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (700, 160), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 60), "Scanned refund policy allows cancellation within 14 days.", fill="black")
    image.save(path)


def create_scanned_pdf(pdf_path: Path, image_path: Path) -> None:
    import fitz

    create_text_image(image_path)
    document = fitz.open()
    page = document.new_page(width=700, height=160)
    page.insert_image(fitz.Rect(0, 0, 700, 160), filename=str(image_path))
    document.save(pdf_path)
    document.close()


def build_minimal_pdf(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 700 Td ({escaped_text}) Tj ET".encode()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/MediaBox [0 0 612 792] /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_position = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())

    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_position}\n%%EOF\n"
        ).encode()
    )

    return bytes(output)
