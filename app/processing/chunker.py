from __future__ import annotations

import re
from dataclasses import replace

from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument
from app.models.chunk import ChunkingConfig, ChunkResult

_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_PARAGRAPH_SPLIT_PATTERN = re.compile(r"\n\s*\n+")


def estimate_token_count(text: str) -> int:
    return len(_TOKEN_PATTERN.findall(text))


def split_paragraphs(text: str) -> list[tuple[str, int, int]]:
    paragraphs: list[tuple[str, int, int]] = []

    cursor = 0
    for match in _PARAGRAPH_SPLIT_PATTERN.finditer(text):
        raw_paragraph = text[cursor : match.start()]
        stripped = raw_paragraph.strip()

        if stripped:
            start = cursor + raw_paragraph.index(stripped)
            end = start + len(stripped)
            paragraphs.append((stripped, start, end))

        cursor = match.end()

    raw_paragraph = text[cursor:]
    stripped = raw_paragraph.strip()

    if stripped:
        start = cursor + raw_paragraph.index(stripped)
        end = start + len(stripped)
        paragraphs.append((stripped, start, end))

    return paragraphs


def split_large_text_by_tokens(text: str, max_tokens: int) -> list[tuple[str, int, int]]:
    matches = list(_TOKEN_PATTERN.finditer(text))

    if not matches:
        return []

    parts: list[tuple[str, int, int]] = []

    for start_token_index in range(0, len(matches), max_tokens):
        end_token_index = min(start_token_index + max_tokens, len(matches))
        start_offset = matches[start_token_index].start()
        end_offset = matches[end_token_index - 1].end()

        part = text[start_offset:end_offset].strip()
        if part:
            parts.append((part, start_offset, end_offset))

    return parts


def _merge_segments_into_chunks(
    segments: list[tuple[str, int, int]],
    config: ChunkingConfig,
) -> list[tuple[str, int, int, int]]:
    chunks: list[tuple[str, int, int, int]] = []

    current_parts: list[str] = []
    current_start: int | None = None
    current_end: int | None = None
    current_tokens = 0

    for segment_text, segment_start, segment_end in segments:
        segment_tokens = estimate_token_count(segment_text)

        if segment_tokens > config.max_tokens:
            if current_parts and current_start is not None and current_end is not None:
                chunks.append(
                    (
                        "\n\n".join(current_parts),
                        current_start,
                        current_end,
                        current_tokens,
                    )
                )
                current_parts = []
                current_start = None
                current_end = None
                current_tokens = 0

            for part_text, part_start, part_end in split_large_text_by_tokens(
                segment_text,
                config.max_tokens,
            ):
                chunks.append(
                    (
                        part_text,
                        segment_start + part_start,
                        segment_start + part_end,
                        estimate_token_count(part_text),
                    )
                )

            continue

        would_exceed = current_tokens + segment_tokens > config.max_tokens

        if would_exceed and current_parts and current_start is not None and current_end is not None:
            chunks.append(
                (
                    "\n\n".join(current_parts),
                    current_start,
                    current_end,
                    current_tokens,
                )
            )

            overlap_parts = _select_overlap_parts(current_parts, config.overlap_tokens)
            current_parts = overlap_parts
            current_tokens = (
                estimate_token_count("\n\n".join(current_parts)) if current_parts else 0
            )

            if current_parts:
                current_start = current_end
            else:
                current_start = None
                current_end = None

        if current_start is None:
            current_start = segment_start

        current_parts.append(segment_text)
        current_end = segment_end
        current_tokens += segment_tokens

    if current_parts and current_start is not None and current_end is not None:
        chunks.append(
            (
                "\n\n".join(current_parts),
                current_start,
                current_end,
                estimate_token_count("\n\n".join(current_parts)),
            )
        )

    return chunks


def _select_overlap_parts(parts: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0:
        return []

    selected: list[str] = []
    total_tokens = 0

    for part in reversed(parts):
        part_tokens = estimate_token_count(part)

        if total_tokens + part_tokens > overlap_tokens and selected:
            break

        selected.insert(0, part)
        total_tokens += part_tokens

        if total_tokens >= overlap_tokens:
            break

    return selected


def chunk_text_block(
    block: ExtractedTextBlock,
    block_index: int,
    source_type: InputType,
    config: ChunkingConfig,
) -> list[ChunkResult]:
    base_offset = block.source_start_offset or 0
    paragraphs = split_paragraphs(block.text)

    if not paragraphs:
        return []

    raw_chunks = _merge_segments_into_chunks(paragraphs, config)

    results: list[ChunkResult] = []
    for local_chunk_index, (chunk_text, start, end, token_count) in enumerate(raw_chunks):
        metadata = {
            **block.metadata,
            "block_index": block_index,
            "local_chunk_index": local_chunk_index,
            "source_type": block.metadata.get("source_type", source_type.value),
            "chunk_strategy": "paragraph_token_window",
        }

        results.append(
            ChunkResult(
                text=chunk_text,
                source_page=block.source_page,
                source_start_offset=base_offset + start,
                source_end_offset=base_offset + end,
                token_count=token_count,
                metadata=metadata,
            )
        )

    return results


def chunk_document(
    document: NormalizedDocument,
    config: ChunkingConfig | None = None,
) -> list[ChunkResult]:
    active_config = config or ChunkingConfig()

    chunks: list[ChunkResult] = []

    for block_index, block in enumerate(document.blocks):
        block_chunks = chunk_text_block(
            block=block,
            block_index=block_index,
            source_type=document.source_type,
            config=active_config,
        )
        chunks.extend(block_chunks)

    return [
        replace(
            chunk,
            metadata={
                **chunk.metadata,
                "global_chunk_index": global_index,
            },
        )
        for global_index, chunk in enumerate(chunks)
    ]
