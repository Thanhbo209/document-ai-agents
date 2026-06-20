import json
from typing import Any

from pydantic import ValidationError

from app.answers.types import AnswerSource
from app.extraction.schemas import (
    ExtractedField,
    ExtractionEvidence,
    ExtractionFieldSpec,
    ExtractionResult,
    ExtractionSchema,
)


class ExtractionValidationError(ValueError):
    pass


def repair_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()

        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ExtractionValidationError("No valid JSON object found.")

    return cleaned[start : end + 1]


def parse_json_object(raw_text: str) -> dict[str, Any]:
    repaired = repair_json_text(raw_text)

    try:
        parsed = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise ExtractionValidationError(f"Invalid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ExtractionValidationError("Extraction output must be a JSON object.")

    return parsed


def validate_extraction_payload(
    raw_text: str,
    schema: ExtractionSchema,
    sources: list[AnswerSource],
) -> ExtractionResult:
    payload = parse_json_object(raw_text)
    source_by_id = {source.source_id: source for source in sources}
    spec_by_name = {field.name: field for field in schema.fields}

    raw_fields = payload.get("fields")

    if not isinstance(raw_fields, list):
        raise ExtractionValidationError("Extraction output must contain a fields list.")

    extracted_fields: list[ExtractedField] = []

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            raise ExtractionValidationError("Each extracted field must be an object.")

        name = str(raw_field.get("name", ""))
        spec = spec_by_name.get(name)

        if spec is None:
            raise ExtractionValidationError(f"Unknown extracted field: {name}")

        evidence = _build_evidence(
            raw_field=raw_field,
            sources=source_by_id,
            spec=spec,
        )

        extracted_fields.append(
            ExtractedField(
                name=name,
                value=raw_field.get("value"),
                field_type=spec.field_type,
                confidence=float(raw_field.get("confidence", 0.0)),
                evidence=evidence,
                review_flags=list(raw_field.get("review_flags", [])),
            )
        )

    _ensure_all_schema_fields_present(
        schema=schema,
        extracted_fields=extracted_fields,
    )

    try:
        return ExtractionResult(
            schema_name=schema.name,
            fields=extracted_fields,
            review_flags=list(payload.get("review_flags", [])),
        )
    except ValidationError as exc:
        raise ExtractionValidationError(str(exc)) from exc


def _build_evidence(
    raw_field: dict,
    sources: dict[str, AnswerSource],
    spec: ExtractionFieldSpec,
) -> ExtractionEvidence | None:
    value = raw_field.get("value")

    if value in {None, ""}:
        return None

    raw_evidence = raw_field.get("evidence")

    if not isinstance(raw_evidence, dict):
        raise ExtractionValidationError(f"Field '{spec.name}' has value but no evidence object.")

    source_id = str(raw_evidence.get("source_id", ""))
    quote = str(raw_evidence.get("quote", "")).strip()

    source = sources.get(source_id)

    if source is None:
        raise ExtractionValidationError(
            f"Field '{spec.name}' references unknown source: {source_id}"
        )

    if not quote:
        raise ExtractionValidationError(f"Field '{spec.name}' evidence quote cannot be empty.")

    if quote.lower() not in source.text.lower():
        raise ExtractionValidationError(
            f"Field '{spec.name}' evidence quote is not found in source {source_id}."
        )

    return ExtractionEvidence(
        source_id=source.source_id,
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        workspace_id=source.workspace_id,
        quote=quote,
        source_page=source.source_page,
        source_start_offset=source.source_start_offset,
        source_end_offset=source.source_end_offset,
    )


def _ensure_all_schema_fields_present(
    schema: ExtractionSchema,
    extracted_fields: list[ExtractedField],
) -> None:
    expected_names = {field.name for field in schema.fields}
    actual_names = {field.name for field in extracted_fields}
    missing = expected_names - actual_names

    if missing:
        raise ExtractionValidationError(f"Missing extracted fields: {', '.join(sorted(missing))}")
