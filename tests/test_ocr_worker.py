import json
from pathlib import Path

from app.ingestion.ocr import OcrBoundingBox, OcrLine, OcrPageResult, OcrToken
from app.storage.artifacts import ArtifactStorage
from app.workers.ocr_worker import OcrWorker
from tests.test_ocr_ingestion import create_scanned_pdf, create_text_image


class FakeOcrEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, int]] = []

    def extract_page(self, image_path: Path, page_number: int) -> OcrPageResult:
        self.calls.append((image_path, page_number))
        bbox = OcrBoundingBox(x=5, y=10, width=300, height=20)
        token = OcrToken(
            text="Scanned refund policy allows cancellation within 14 days.",
            confidence=0.91,
            bbox=bbox,
        )
        line = OcrLine(
            text=token.text,
            confidence=0.91,
            bbox=bbox,
            tokens=[token],
        )

        return OcrPageResult(
            page_number=page_number,
            text=line.text,
            confidence=0.91,
            lines=[line],
            low_confidence=False,
            image_path=str(image_path),
        )


def test_ocr_worker_processes_scanned_pdf_and_writes_artifacts(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned.pdf"
    create_scanned_pdf(pdf_path, tmp_path / "scan.png")
    storage = ArtifactStorage(tmp_path / "artifacts")
    engine = FakeOcrEngine()

    blocks = OcrWorker(
        artifact_storage=storage,
        ocr_engine=engine,
    ).process_scanned_pdf(
        workspace_id="workspace-worker",
        document_id="document-worker",
        pdf_path=pdf_path,
    )

    assert engine.calls
    assert len(blocks) == 1
    assert blocks[0].metadata["ocr"] is True
    assert blocks[0].metadata["bounding_boxes"][0]["bbox"]["width"] == 300
    assert storage.ocr_page_image_path("workspace-worker", "document-worker", 1).exists()
    assert storage.ocr_preprocessed_image_path("workspace-worker", "document-worker", 1).exists()

    ocr_json_path = storage.ocr_json_path("workspace-worker", "document-worker")
    assert ocr_json_path.exists()
    payload = json.loads(ocr_json_path.read_text(encoding="utf-8"))
    assert payload["pages"][0]["confidence"] == 0.91


def test_ocr_worker_processes_image_and_writes_artifacts(tmp_path: Path) -> None:
    image_path = tmp_path / "scan.png"
    create_text_image(image_path)
    storage = ArtifactStorage(tmp_path / "artifacts")
    engine = FakeOcrEngine()

    blocks = OcrWorker(
        artifact_storage=storage,
        ocr_engine=engine,
    ).process_image(
        workspace_id="workspace-image",
        document_id="document-image",
        image_path=image_path,
    )

    assert engine.calls == [
        (
            storage.ocr_preprocessed_image_path("workspace-image", "document-image", 1),
            1,
        )
    ]
    assert len(blocks) == 1
    assert blocks[0].metadata["source_type"] == "image"
    assert storage.ocr_page_image_path("workspace-image", "document-image", 1).exists()
    assert storage.ocr_json_path("workspace-image", "document-image").exists()
