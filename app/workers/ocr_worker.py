import json
import shutil
from dataclasses import replace
from pathlib import Path

from app.ingestion.ocr import (
    OcrEngine,
    OcrPageResult,
    ocr_results_to_jsonable,
    ocr_results_to_text_blocks,
    preprocess_image_for_ocr,
    render_pdf_pages_for_ocr,
)
from app.ingestion.types import ExtractedTextBlock
from app.storage.artifacts import ArtifactStorage


class OcrWorker:
    def __init__(
        self,
        artifact_storage: ArtifactStorage,
        ocr_engine: OcrEngine,
    ) -> None:
        self.artifact_storage = artifact_storage
        self.ocr_engine = ocr_engine

    def process_scanned_pdf(
        self,
        workspace_id: str,
        document_id: str,
        pdf_path: Path,
    ) -> list[ExtractedTextBlock]:
        ocr_dir = self.artifact_storage.ocr_dir(workspace_id, document_id)
        page_images = render_pdf_pages_for_ocr(pdf_path, ocr_dir)
        results = self._extract_pages(
            workspace_id=workspace_id,
            document_id=document_id,
            page_images=page_images,
        )
        self._write_ocr_json(workspace_id, document_id, results)

        return ocr_results_to_text_blocks(results, source_type="ocr_pdf")

    def process_image(
        self,
        workspace_id: str,
        document_id: str,
        image_path: Path,
    ) -> list[ExtractedTextBlock]:
        artifact_image = self.artifact_storage.ocr_page_image_path(
            workspace_id,
            document_id,
            page_number=1,
        )
        artifact_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image_path, artifact_image)

        results = self._extract_pages(
            workspace_id=workspace_id,
            document_id=document_id,
            page_images=[artifact_image],
        )
        self._write_ocr_json(workspace_id, document_id, results)

        return ocr_results_to_text_blocks(results, source_type="image")

    def _extract_pages(
        self,
        workspace_id: str,
        document_id: str,
        page_images: list[Path],
    ) -> list[OcrPageResult]:
        results: list[OcrPageResult] = []

        for page_number, page_image in enumerate(page_images, start=1):
            preprocessed_path = self.artifact_storage.ocr_preprocessed_image_path(
                workspace_id,
                document_id,
                page_number=page_number,
            )
            preprocess_image_for_ocr(page_image, preprocessed_path)
            result = self.ocr_engine.extract_page(preprocessed_path, page_number)

            if result.image_path is None:
                result = replace(result, image_path=str(preprocessed_path))

            results.append(result)

        return results

    def _write_ocr_json(
        self,
        workspace_id: str,
        document_id: str,
        results: list[OcrPageResult],
    ) -> None:
        ocr_json_path = self.artifact_storage.ocr_json_path(workspace_id, document_id)
        self.artifact_storage.write_text(
            ocr_json_path,
            json.dumps({"pages": ocr_results_to_jsonable(results)}, indent=2),
        )
