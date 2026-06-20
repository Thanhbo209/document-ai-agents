from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    max_tokens: int = 300
    overlap_tokens: int = 40

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than 0.")

        if self.overlap_tokens < 0:
            raise ValueError("overlap_tokens cannot be negative.")

        if self.overlap_tokens >= self.max_tokens:
            raise ValueError("overlap_tokens must be smaller than max_tokens.")


@dataclass(frozen=True)
class ChunkResult:
    text: str
    source_page: int | None
    source_start_offset: int | None
    source_end_offset: int | None
    token_count: int
    metadata: dict
