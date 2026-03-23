from app.models.schemas import QueryRewritePlan, SearchResult
from app.services.ranker import SearchRanker


rewrite_plan = QueryRewritePlan(
    search_terms=["ai regulation latest news", "eu ai act updates"],
    time_filter="week",
    language="en",
    topic="AI regulation",
)


def test_ranking_uses_embeddings_when_available() -> None:
    ranker = SearchRanker()
    results = [
        SearchResult(title="AI regulation update", url="https://example.com/a", snippet="Policy shift", source="Example"),
        SearchResult(title="Sports roundup", url="https://example.com/b", snippet="Match recap", source="Example"),
    ]
    embeddings = [
        [1.0, 0.0],
        [0.9, 0.1],
        [0.0, 1.0],
    ]

    ranked = ranker.rank("AI regulation", rewrite_plan, results, embeddings, max_results=2)

    assert ranked[0].title == "AI regulation update"
    assert ranked[0].ranking_reason == "embedding_similarity+keyword_bonus"
    assert ranked[0].score > ranked[1].score


def test_ranking_falls_back_to_heuristics() -> None:
    ranker = SearchRanker()
    results = [
        SearchResult(title="EU AI Act reaches new milestone", url="https://example.com/a", snippet="Regulators moved forward.", source="Example"),
        SearchResult(title="Cooking trends", url="https://example.com/b", snippet="A story about recipes.", source="Food"),
    ]

    ranked = ranker.rank("AI regulation", rewrite_plan, results, embeddings=None, max_results=2)

    assert ranked[0].title == "EU AI Act reaches new milestone"
    assert ranked[0].ranking_reason == "keyword_overlap_heuristic"
