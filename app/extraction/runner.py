import json
import re
from typing import Protocol

from app.answers.types import AnswerSource
from app.extraction.schemas import ExtractionFieldSpec, ExtractionFieldType, ExtractionSchema
from app.extraction.validators import validate_extraction_payload

_DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")
_AMOUNT_PATTERN = re.compile(r"(?:\$|USD\s*)\d+(?:,\d{3})*(?:\.\d{2})?")
_NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")


class StructuredExtractionClient(Protocol):
    model_name: str

    def extract_json(
        self,
        schema: ExtractionSchema,
        sources: list[AnswerSource],
    ) -> str:
        pass


class LocalStructuredExtractionClient:
    model_name = "local-structured-extractor-v1"

    def extract_json(
        self,
        schema: ExtractionSchema,
        sources: list[AnswerSource],
    ) -> str:
        fields = []

        for spec in schema.fields:
            fields.append(_extract_field(spec, sources))

        return json.dumps(
            {
                "fields": fields,
                "review_flags": [],
            }
        )


class StructuredExtractionRunner:
    def __init__(self, client: StructuredExtractionClient) -> None:
        self.client = client

    def run(
        self,
        schema: ExtractionSchema,
        sources: list[AnswerSource],
    ):
        raw_output = self.client.extract_json(
            schema=schema,
            sources=sources,
        )

        return validate_extraction_payload(
            raw_text=raw_output,
            schema=schema,
            sources=sources,
        )


def _extract_field(
    spec: ExtractionFieldSpec,
    sources: list[AnswerSource],
) -> dict:
    for source in sources:
        extracted = _extract_from_source(spec, source)

        if extracted is not None:
            value, quote, confidence = extracted

            return {
                "name": spec.name,
                "value": value,
                "confidence": confidence,
                "evidence": {
                    "source_id": source.source_id,
                    "quote": quote,
                },
                "review_flags": [],
            }

    return {
        "name": spec.name,
        "value": None,
        "confidence": 0.0,
        "evidence": None,
        "review_flags": ["missing_evidence"],
    }


def _extract_from_source(
    spec: ExtractionFieldSpec,
    source: AnswerSource,
) -> tuple[object, str, float] | None:
    text = source.text
    lowered_name = spec.name.lower()

    if spec.field_type == ExtractionFieldType.DATE:
        return _extract_regex_value(_DATE_PATTERN, text)

    if spec.field_type == ExtractionFieldType.AMOUNT:
        return _extract_regex_value(_AMOUNT_PATTERN, text)

    if spec.field_type == ExtractionFieldType.NUMBER:
        return _extract_regex_value(_NUMBER_PATTERN, text)

    if spec.field_type == ExtractionFieldType.BOOLEAN:
        return _extract_boolean(text)

    if spec.field_type == ExtractionFieldType.TEXT:
        return _extract_named_text_field(lowered_name, text)

    if spec.field_type == ExtractionFieldType.LIST:
        return _extract_list(text)

    return None


def _extract_regex_value(
    pattern: re.Pattern,
    text: str,
) -> tuple[str, str, float] | None:
    match = pattern.search(text)

    if match is None:
        return None

    value = match.group(0)

    return value, _sentence_containing(text, value), 0.85


def _extract_boolean(text: str) -> tuple[bool, str, float] | None:
    lowered = text.lower()

    yes_markers = ["must", "required", "shall", "is required"]
    no_markers = ["not required", "optional", "not mandatory"]

    for marker in no_markers:
        if marker in lowered:
            return False, _sentence_containing(text, marker), 0.75

    for marker in yes_markers:
        if marker in lowered:
            return True, _sentence_containing(text, marker), 0.75

    return None


def _extract_named_text_field(
    field_name: str,
    text: str,
) -> tuple[str, str, float] | None:
    label_candidates = [
        field_name,
        field_name.replace("_", " "),
        field_name.replace("_", "-"),
    ]

    for label in label_candidates:
        pattern = re.compile(
            rf"\b{re.escape(label)}\b\s*:\s*(.+)",
            re.IGNORECASE,
        )
        match = pattern.search(text)

        if match is not None:
            value = match.group(1).strip().split("\n")[0].strip()

            return value, _sentence_containing(text, value), 0.8

    return None


def _extract_list(text: str) -> tuple[list[str], str, float] | None:
    bullet_lines = [
        line.strip("-*• ").strip()
        for line in text.splitlines()
        if line.strip().startswith(("-", "*", "•"))
    ]

    values = [line for line in bullet_lines if line]

    if not values:
        return None

    quote = "\n".join(values[:3])

    return values, quote, 0.7


def _sentence_containing(text: str, value: object) -> str:
    value_text = str(value)

    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if value_text.lower() in sentence.lower():
            return sentence.strip()

    return value_text
