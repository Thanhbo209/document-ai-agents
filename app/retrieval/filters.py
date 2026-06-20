from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalFilters:
    document_ids: list[str] | None = None
    chunk_ids: list[str] | None = None
    source_pages: list[int] | None = None

    def to_metadata_filter(self) -> dict[str, object]:
        metadata_filter: dict[str, object] = {}

        if self.document_ids:
            metadata_filter["document_id"] = self.document_ids

        if self.chunk_ids:
            metadata_filter["chunk_id"] = self.chunk_ids

        if self.source_pages:
            metadata_filter["source_page"] = self.source_pages

        return metadata_filter
