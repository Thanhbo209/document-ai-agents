import re

from app.answers.types import AnswerCitation, AnswerSource

_CITATION_PATTERN = re.compile(r"\[S(\d+)\]")
_SENTENCE_PATTERN = re.compile(r"[^.!?\n]+[.!?]?")


class CitationValidationError(ValueError):
    pass


def extract_source_refs(message: str) -> list[str]:
    refs = _CITATION_PATTERN.findall(message)
    seen: set[str] = set()
    ordered_refs: list[str] = []

    for ref in refs:
        source_id = f"S{ref}"

        if source_id not in seen:
            seen.add(source_id)
            ordered_refs.append(source_id)

    return ordered_refs


def validate_cited_claims(message: str) -> None:
    claim_sentences = _claim_sentences(message)

    for sentence in claim_sentences:
        if not _CITATION_PATTERN.search(sentence):
            raise CitationValidationError(f"Uncited claim detected: {sentence.strip()}")


def build_citations_from_message(
    message: str,
    sources: list[AnswerSource],
) -> list[AnswerCitation]:
    refs = extract_source_refs(message)
    source_by_id = {source.source_id: source for source in sources}

    citations: list[AnswerCitation] = []

    for ref in refs:
        source = source_by_id.get(ref)

        if source is None:
            raise CitationValidationError(f"Unknown citation reference: [{ref}]")

        citations.append(
            AnswerCitation(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                workspace_id=source.workspace_id,
                source_page=source.source_page,
                source_start_offset=source.source_start_offset,
                source_end_offset=source.source_end_offset,
                quote=_short_quote(source.text),
                metadata=source.metadata,
            )
        )

    return citations


def _claim_sentences(message: str) -> list[str]:
    sentences: list[str] = []

    for match in _SENTENCE_PATTERN.finditer(message):
        sentence = match.group(0).strip()

        if not sentence:
            continue

        if _is_non_claim(sentence):
            continue

        sentences.append(sentence)

    return sentences


def _is_non_claim(sentence: str) -> bool:
    lowered = sentence.lower()

    if lowered.startswith("i don't have enough evidence"):
        return True

    if lowered.startswith("not enough evidence"):
        return True

    if lowered in {"sources:", "source:"}:
        return True

    return False


def _short_quote(text: str, max_length: int = 240) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_length:
        return cleaned

    return f"{cleaned[: max_length - 3]}..."
