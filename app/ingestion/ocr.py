from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from app.ingestion.errors import ExtractionError
from app.ingestion.types import ExtractedTextBlock

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.65
MAX_BOUNDING_BOX_LINES = 200


class OcrError(ValueError):
    pass


class OcrEngineUnavailableError(OcrError):
    def __init__(self) -> None:
        super().__init__("OCR engine unavailable. Install Tesseract or disable OCR.")


@dataclass(frozen=True)
class OcrBoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class OcrToken:
    text: str
    confidence: float
    bbox: OcrBoundingBox


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float
    bbox: OcrBoundingBox
    tokens: list[OcrToken]


@dataclass(frozen=True)
class OcrPageResult:
    page_number: int
    text: str
    confidence: float
    lines: list[OcrLine]
    low_confidence: bool
    image_path: str | None = None


class OcrEngine(Protocol):
    def extract_page(
        self,
        image_path: Path,
        page_number: int,
    ) -> OcrPageResult: ...


class TesseractOcrEngine:
    def __init__(
        self,
        low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.low_confidence_threshold = low_confidence_threshold

    def extract_page(
        self,
        image_path: Path,
        page_number: int,
    ) -> OcrPageResult:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise OcrEngineUnavailableError() from exc

        try:
            with Image.open(image_path) as image:
                data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT,
                )
        except pytesseract.TesseractNotFoundError as exc:
            raise OcrEngineUnavailableError() from exc
        except FileNotFoundError as exc:
            raise OcrEngineUnavailableError() from exc
        except Exception as exc:
            raise OcrError(f"OCR failed for page {page_number}: {exc}") from exc

        lines = _lines_from_tesseract_data(data)
        valid_confidences = [
            token.confidence for line in lines for token in line.tokens if token.text.strip()
        ]
        confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0
        text = "\n".join(line.text for line in lines if line.text.strip())

        return OcrPageResult(
            page_number=page_number,
            text=text,
            confidence=confidence,
            lines=lines,
            low_confidence=confidence < self.low_confidence_threshold,
            image_path=str(image_path),
        )


def preprocess_image_for_ocr(input_path: Path, output_path: Path) -> Path:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise ExtractionError("OCR preprocessing requires Pillow.") from exc

    try:
        with Image.open(input_path) as image:
            processed = ImageOps.autocontrast(image.convert("L"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            processed.save(output_path, format="PNG")
    except OSError as exc:
        raise ExtractionError(f"Could not preprocess image for OCR: {exc}") from exc

    return output_path


def render_pdf_pages_for_ocr(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 200,
) -> list[Path]:
    try:
        import fitz
    except ImportError as exc:
        raise ExtractionError("PDF OCR rendering requires pymupdf.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)

    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise ExtractionError(f"Could not open PDF for OCR rendering: {exc}") from exc

    try:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_dir / f"page-{page_index:03d}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)
    finally:
        document.close()

    return image_paths


def ocr_results_to_text_blocks(
    results: list[OcrPageResult],
    source_type: str,
) -> list[ExtractedTextBlock]:
    blocks: list[ExtractedTextBlock] = []

    for result in results:
        if not result.text.strip():
            continue

        text = f"OCR Page {result.page_number}\n\n{result.text.strip()}"
        bounding_boxes = [
            {
                "text": line.text,
                "confidence": line.confidence,
                "bbox": asdict(line.bbox),
            }
            for line in result.lines[:MAX_BOUNDING_BOX_LINES]
            if line.text.strip()
        ]

        blocks.append(
            ExtractedTextBlock(
                text=text,
                source_page=result.page_number,
                source_start_offset=0,
                source_end_offset=len(text),
                metadata={
                    "source_type": source_type,
                    "page_number": result.page_number,
                    "ocr": True,
                    "ocr_confidence": result.confidence,
                    "low_confidence": result.low_confidence,
                    "image_path": result.image_path,
                    "bounding_boxes": bounding_boxes,
                    "bounding_boxes_truncated": len(result.lines) > MAX_BOUNDING_BOX_LINES,
                },
            )
        )

    return blocks


def ocr_results_to_jsonable(results: list[OcrPageResult]) -> list[dict]:
    return [asdict(result) for result in results]


def _lines_from_tesseract_data(data: dict) -> list[OcrLine]:
    grouped_tokens: dict[tuple[int, int, int], list[OcrToken]] = defaultdict(list)
    count = len(data.get("text", []))

    for index in range(count):
        text = str(data["text"][index]).strip()
        confidence = _parse_confidence(data["conf"][index])

        if not text or confidence is None:
            continue

        key = (
            int(data["block_num"][index]),
            int(data["par_num"][index]),
            int(data["line_num"][index]),
        )
        grouped_tokens[key].append(
            OcrToken(
                text=text,
                confidence=confidence,
                bbox=OcrBoundingBox(
                    x=int(data["left"][index]),
                    y=int(data["top"][index]),
                    width=int(data["width"][index]),
                    height=int(data["height"][index]),
                ),
            )
        )

    lines: list[OcrLine] = []

    for key in sorted(grouped_tokens):
        tokens = grouped_tokens[key]
        line_text = " ".join(token.text for token in tokens)
        line_confidence = sum(token.confidence for token in tokens) / len(tokens)
        lines.append(
            OcrLine(
                text=line_text,
                confidence=line_confidence,
                bbox=_union_bbox([token.bbox for token in tokens]),
                tokens=tokens,
            )
        )

    return lines


def _parse_confidence(value: object) -> float | None:
    try:
        raw_confidence = float(value)
    except TypeError, ValueError:
        return None

    if raw_confidence < 0:
        return None

    confidence = raw_confidence / 100 if raw_confidence > 1 else raw_confidence
    return max(0.0, min(1.0, confidence))


def _union_bbox(boxes: list[OcrBoundingBox]) -> OcrBoundingBox:
    left = min(box.x for box in boxes)
    top = min(box.y for box in boxes)
    right = max(box.x + box.width for box in boxes)
    bottom = max(box.y + box.height for box in boxes)

    return OcrBoundingBox(
        x=left,
        y=top,
        width=right - left,
        height=bottom - top,
    )
