import pytest

from app.ingestion.types import ExtractedTextBlock, InputType, NormalizedDocument
from app.models.chunk import ChunkingConfig
from app.processing.chunker import chunk_document, estimate_token_count, split_paragraphs


def test_estimate_token_count_is_deterministic() -> None:
    text = "Hello, world! This is RAG."

    assert estimate_token_count(text) == estimate_token_count(text)
    assert estimate_token_count(text) == 8


def test_split_paragraphs_preserves_offsets() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\nThird."

    paragraphs = split_paragraphs(text)

    assert paragraphs == [
        ("First paragraph.", 0, 16),
        ("Second paragraph.", 18, 35),
        ("Third.", 37, 43),
    ]


def test_chunk_document_keeps_small_text_as_single_chunk() -> None:
    document = NormalizedDocument(
        title="Notes",
        source_type=InputType.TEXT,
        blocks=[
            ExtractedTextBlock(
                text="Alpha paragraph.\n\nBeta paragraph.",
                source_page=None,
                source_start_offset=0,
                source_end_offset=33,  # <-- Fixed string length here
                metadata={"filename": "notes.txt"},
            )
        ],
    )

    chunks = chunk_document(document, ChunkingConfig(max_tokens=50, overlap_tokens=5))

    assert len(chunks) == 1
    assert chunks[0].text == "Alpha paragraph.\n\nBeta paragraph."
    assert chunks[0].source_page is None
    assert chunks[0].source_start_offset == 0
    assert chunks[0].source_end_offset == 33  # <-- Fixed assertion here


def test_chunk_document_splits_by_paragraph_token_budget() -> None:
    document = NormalizedDocument(
        title="Long Notes",
        source_type=InputType.TEXT,
        blocks=[
            ExtractedTextBlock(
                text="One two three.\n\nFour five six.\n\nSeven eight nine.",
                source_page=None,
                source_start_offset=0,
                source_end_offset=52,
                metadata={"filename": "notes.txt"},
            )
        ],
    )

    chunks = chunk_document(document, ChunkingConfig(max_tokens=6, overlap_tokens=0))

    assert [chunk.text for chunk in chunks] == [
        "One two three.",
        "Four five six.",
        "Seven eight nine.",
    ]
    assert [chunk.metadata["global_chunk_index"] for chunk in chunks] == [0, 1, 2]


def test_chunk_document_preserves_pdf_page_metadata() -> None:
    document = NormalizedDocument(
        title="Paper",
        source_type=InputType.PDF,
        blocks=[
            ExtractedTextBlock(
                text="Page one text.",
                source_page=1,
                source_start_offset=0,
                source_end_offset=14,
                metadata={
                    "filename": "paper.pdf",
                    "page_number": 1,
                },
            ),
            ExtractedTextBlock(
                text="Page two text.",
                source_page=2,
                source_start_offset=0,
                source_end_offset=14,
                metadata={
                    "filename": "paper.pdf",
                    "page_number": 2,
                },
            ),
        ],
    )

    chunks = chunk_document(document, ChunkingConfig(max_tokens=50, overlap_tokens=5))

    assert len(chunks) == 2
    assert chunks[0].source_page == 1
    assert chunks[0].metadata["page_number"] == 1
    assert chunks[1].source_page == 2
    assert chunks[1].metadata["page_number"] == 2


def test_chunking_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        ChunkingConfig(max_tokens=0, overlap_tokens=0)

    with pytest.raises(ValueError):
        ChunkingConfig(max_tokens=10, overlap_tokens=-1)

    with pytest.raises(ValueError):
        ChunkingConfig(max_tokens=10, overlap_tokens=10)
