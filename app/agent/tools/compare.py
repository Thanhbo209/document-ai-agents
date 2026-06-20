from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.answers.types import AnswerSource


class ComparisonStatus(StrEnum):
    SAME = "same"
    CHANGED = "changed"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"


class ComparisonInputError(ValueError):
    pass


@dataclass(frozen=True)
class DocumentSide:
    label: str
    document_id: str
    sources: list[AnswerSource]


@dataclass(frozen=True)
class EvidenceRef:
    side: str
    source_id: str
    chunk_id: str
    document_id: str
    workspace_id: str
    quote: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    metadata: dict


@dataclass(frozen=True)
class ComparisonItem:
    key: str
    status: ComparisonStatus
    summary: str
    left_value: str | None
    right_value: str | None
    left_evidence: EvidenceRef | None
    right_evidence: EvidenceRef | None


@dataclass(frozen=True)
class ComparisonResult:
    left_document_id: str
    right_document_id: str
    left_label: str
    right_label: str
    items: list[ComparisonItem]
    evidence_appendix: list[EvidenceRef]
    review_flags: list[str]


@dataclass(frozen=True)
class _ExtractedFact:
    key: str
    value: str
    evidence: EvidenceRef


_KEY_VALUE_PATTERN = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 _/-]{1,80})\s*:\s*(?P<value>.+)$")


class DocumentComparisonTool:
    def compare(
        self,
        left: DocumentSide,
        right: DocumentSide,
        fields: list[str] | None = None,
    ) -> ComparisonResult:
        _validate_side(left)
        _validate_side(right)

        left_facts = _extract_facts(left)
        right_facts = _extract_facts(right)

        keys = _comparison_keys(
            left_facts=left_facts,
            right_facts=right_facts,
            fields=fields,
        )

        items = [
            _compare_key(
                key=key,
                left_facts=left_facts,
                right_facts=right_facts,
            )
            for key in keys
        ]

        review_flags = _review_flags(items)

        return ComparisonResult(
            left_document_id=left.document_id,
            right_document_id=right.document_id,
            left_label=left.label,
            right_label=right.label,
            items=items,
            evidence_appendix=_build_evidence_appendix(left=left, right=right),
            review_flags=review_flags,
        )


def _validate_side(side: DocumentSide) -> None:
    if not side.document_id.strip():
        raise ComparisonInputError("Document side must have a document_id.")

    if not side.sources:
        raise ComparisonInputError(
            f"Document '{side.document_id}' must include at least one source."
        )

    for source in side.sources:
        if source.document_id != side.document_id:
            raise ComparisonInputError(
                f"Source {source.source_id} does not belong to document {side.document_id}."
            )


def _extract_facts(side: DocumentSide) -> dict[str, _ExtractedFact]:
    facts: dict[str, _ExtractedFact] = {}

    for source in side.sources:
        for line in source.text.splitlines():
            clean_line = line.strip()

            if not clean_line:
                continue

            match = _KEY_VALUE_PATTERN.match(clean_line)

            if match is None:
                continue

            key = _normalize_key(match.group("key"))
            value = _clean_value(match.group("value"))

            if not key or not value:
                continue

            if key in facts:
                continue

            facts[key] = _ExtractedFact(
                key=key,
                value=value,
                evidence=_evidence_from_source(
                    side_label=side.label,
                    source=source,
                    quote=clean_line,
                ),
            )

    return facts


def _comparison_keys(
    left_facts: dict[str, _ExtractedFact],
    right_facts: dict[str, _ExtractedFact],
    fields: list[str] | None,
) -> list[str]:
    if fields:
        return [_normalize_key(field) for field in fields]

    return sorted(set(left_facts) | set(right_facts))


def _compare_key(
    key: str,
    left_facts: dict[str, _ExtractedFact],
    right_facts: dict[str, _ExtractedFact],
) -> ComparisonItem:
    left_fact = left_facts.get(key)
    right_fact = right_facts.get(key)

    if left_fact is not None and right_fact is not None:
        if _normalize_value(left_fact.value) == _normalize_value(right_fact.value):
            status = ComparisonStatus.SAME
            summary = f"{_display_key(key)} is the same in both documents."
        else:
            status = ComparisonStatus.CHANGED
            summary = (
                f"{_display_key(key)} changed from '{left_fact.value}' to '{right_fact.value}'."
            )

        return ComparisonItem(
            key=key,
            status=status,
            summary=summary,
            left_value=left_fact.value,
            right_value=right_fact.value,
            left_evidence=left_fact.evidence,
            right_evidence=right_fact.evidence,
        )

    if left_fact is not None:
        return ComparisonItem(
            key=key,
            status=ComparisonStatus.ONLY_LEFT,
            summary=f"{_display_key(key)} appears only in the left document.",
            left_value=left_fact.value,
            right_value=None,
            left_evidence=left_fact.evidence,
            right_evidence=None,
        )

    if right_fact is not None:
        return ComparisonItem(
            key=key,
            status=ComparisonStatus.ONLY_RIGHT,
            summary=f"{_display_key(key)} appears only in the right document.",
            left_value=None,
            right_value=right_fact.value,
            left_evidence=None,
            right_evidence=right_fact.evidence,
        )

    return ComparisonItem(
        key=key,
        status=ComparisonStatus.CHANGED,
        summary=f"{_display_key(key)} was requested but not found in either document.",
        left_value=None,
        right_value=None,
        left_evidence=None,
        right_evidence=None,
    )


def _evidence_from_source(
    side_label: str,
    source: AnswerSource,
    quote: str | None = None,
) -> EvidenceRef:
    return EvidenceRef(
        side=side_label,
        source_id=source.source_id,
        chunk_id=source.chunk_id,
        document_id=source.document_id,
        workspace_id=source.workspace_id,
        quote=quote or _short_quote(source.text),
        source_page=source.source_page,
        source_start_offset=source.source_start_offset,
        source_end_offset=source.source_end_offset,
        metadata=source.metadata,
    )


def _build_evidence_appendix(
    left: DocumentSide,
    right: DocumentSide,
) -> list[EvidenceRef]:
    appendix: list[EvidenceRef] = []

    for side in [left, right]:
        for source in side.sources:
            appendix.append(
                _evidence_from_source(
                    side_label=side.label,
                    source=source,
                )
            )

    return appendix


def _review_flags(items: list[ComparisonItem]) -> list[str]:
    flags: list[str] = []

    if not items:
        flags.append("no_comparable_fields")

    if any(item.status == ComparisonStatus.CHANGED for item in items):
        flags.append("differences_found")

    if any(
        item.status in {ComparisonStatus.ONLY_LEFT, ComparisonStatus.ONLY_RIGHT} for item in items
    ):
        flags.append("missing_fields_found")

    return flags


def _normalize_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", normalized)


def _display_key(value: str) -> str:
    return value.replace("_", " ")


def _clean_value(value: str) -> str:
    return value.strip().strip(" .")


def _normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip())


def _short_quote(text: str, max_length: int = 260) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_length:
        return cleaned

    return f"{cleaned[: max_length - 3]}..."
