import re
from collections.abc import Generator
from typing import Protocol

from app.answers.types import AnswerSource

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
_SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]?")


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
            for sentence in _sentences(source.text):
                sentence_terms = _important_terms(sentence)

                if query_terms & sentence_terms:
                    cited_sentences.append(f"{sentence} [{source.source_id}]")

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
    return [
        match.group(0).strip()
        for match in _SENTENCE_PATTERN.finditer(text)
        if match.group(0).strip()
    ]
