import re
from collections.abc import Generator
from typing import Protocol

from app.answers.types import AnswerSource

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
_SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]?")
_MIN_ANSWER_TERMS = 2


class LLMClient(Protocol):
    model_name: str

    def generate_answer(
        self,
        query: str,
        sources: list[AnswerSource],
        prompt: str,
    ) -> str:
        pass

    def stream_answer(
        self,
        query: str,
        sources: list[AnswerSource],
        prompt: str,
    ) -> Generator[str]:
        pass


class LocalGroundedLLMClient:
    model_name = "local-grounded-extractive-v1"

    def generate_answer(
        self,
        query: str,
        sources: list[AnswerSource],
        prompt: str,
    ) -> str:
        del prompt

        query_terms = _important_terms(query)
        cited_sentences: list[str] = []

        for source in sources:
            for evidence_unit in _evidence_units(source.text):
                unit_terms = _important_terms(evidence_unit)

                if not _is_useful_answer_sentence(evidence_unit):
                    continue

                if query_terms & unit_terms:
                    clean_sentence = _clean_sentence(evidence_unit)
                    cited_sentences.append(f"{clean_sentence} [{source.source_id}].")

                if len(cited_sentences) >= 3:
                    break

            if len(cited_sentences) >= 3:
                break

        if not cited_sentences:
            return "I don't have enough evidence in the provided sources to answer that."

        return " ".join(cited_sentences)

    def stream_answer(
        self,
        query: str,
        sources: list[AnswerSource],
        prompt: str,
    ) -> Generator[str]:
        answer = self.generate_answer(
            query=query,
            sources=sources,
            prompt=prompt,
        )

        for token in answer.split(" "):
            yield f"{token} "


def _evidence_units(text: str) -> list[str]:
    units: list[str] = []

    lines = [" ".join(line.split()).strip() for line in text.splitlines() if line.strip()]

    # Handle heading-style documents:
    # Education
    # HCM University...
    for index, line in enumerate(lines):
        if not _looks_like_heading(line):
            continue

        following = _next_useful_line(lines, start_index=index + 1)

        if following is not None:
            units.append(f"{line}: {following}")

    # Also keep normal sentence extraction.
    units.extend(_sentences(text))

    return _dedupe_preserve_order(units)


def _next_useful_line(
    lines: list[str],
    start_index: int,
) -> str | None:
    for line in lines[start_index : start_index + 4]:
        if _looks_like_heading(line):
            continue

        if _is_useful_answer_sentence(line):
            return line

    return None


def _looks_like_heading(line: str) -> bool:
    terms = _important_terms(line)

    if len(terms) == 0:
        return False

    if len(line.split()) > 5:
        return False

    if line.endswith((".", "!", "?", ":")):
        return False

    return True


def _important_terms(text: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "listed",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "who",
        "why",
        "with",
    }

    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) > 2 and token.lower() not in stopwords
    }


def _sentences(text: str) -> list[str]:
    sentences: list[str] = []

    for line in text.splitlines():
        clean_line = " ".join(line.split()).strip()

        if not clean_line:
            continue

        for match in _SENTENCE_PATTERN.finditer(clean_line):
            sentence = match.group(0).strip()

            if sentence:
                sentences.append(sentence)

    return sentences


def _is_useful_answer_sentence(sentence: str) -> bool:
    terms = _important_terms(sentence)

    if len(terms) < _MIN_ANSWER_TERMS:
        return False

    if len(sentence.split()) < 4:
        return False

    return True


def _clean_sentence(sentence: str) -> str:
    return " ".join(sentence.split()).strip().rstrip(".!?")


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result
