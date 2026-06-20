from app.retrieval.reranker import KeywordOverlapReranker
from app.retrieval.types import RetrievedChunk


def make_result(chunk_id: str, text: str, vector_score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        workspace_id="workspace-1",
        text=text,
        vector_score=vector_score,
        rerank_score=None,
        final_score=vector_score,
        source_page=None,
        source_start_offset=0,
        source_end_offset=len(text),
        metadata={},
    )


def test_keyword_overlap_reranker_boosts_query_matches() -> None:
    reranker = KeywordOverlapReranker()

    results = [
        make_result("chunk-1", "unrelated content", 0.9),
        make_result("chunk-2", "refund policy cancellation", 0.8),
    ]

    reranked = reranker.rerank(
        query="refund policy",
        results=results,
        top_k=2,
    )

    assert reranked[0].chunk_id == "chunk-2"
    assert reranked[0].rerank_score == 1.0
    assert reranked[0].final_score > reranked[1].final_score


def test_keyword_overlap_reranker_respects_top_k() -> None:
    reranker = KeywordOverlapReranker()

    results = [
        make_result("chunk-1", "alpha", 0.1),
        make_result("chunk-2", "beta", 0.2),
        make_result("chunk-3", "gamma", 0.3),
    ]

    reranked = reranker.rerank(
        query="gamma",
        results=results,
        top_k=1,
    )

    assert len(reranked) == 1
    assert reranked[0].chunk_id == "chunk-3"
