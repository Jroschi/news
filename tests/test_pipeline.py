import pytest

from app.models.schemas import (
    ArticleContent,
    ArticleSummary,
    QueryRewritePlan,
    RankedSearchResult,
    SearchResult,
    SummarizeRequest,
)
from app.services.pipeline import NewsPipeline
from app.services.ranker import SearchRanker


class FakeSearxNGClient:
    async def search(self, query: str, language: str = "en", limit: int = 10) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"{query} article one",
                url="https://example.com/article-1",
                snippet="Important AI regulation development",
                source="Example",
                published_date="2026-03-22",
            ),
            SearchResult(
                title=f"{query} article two",
                url="https://example.com/article-2",
                snippet="Secondary development",
                source="Example",
            ),
            SearchResult(
                title=f"{query} article three",
                url="https://example.com/article-3",
                snippet="Additional market response coverage",
                source="Example",
                published_date="2026-03-21",
            ),
            SearchResult(
                title=f"{query} article four",
                url="https://example.com/article-4",
                snippet="Background context and analysis",
                source="Example",
            ),
        ]


class FakeOllamaClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [
            [1.0, 0.0],
            [1.0, 0.0],
            [0.95, 0.05],
            [0.9, 0.1],
            [0.85, 0.15],
        ]

    async def summarize_article(self, article_title: str, article_text: str) -> ArticleSummary:
        return ArticleSummary(
            summary=[
                f"Summary for {article_title}",
                "The article discusses regulation.",
                "Companies may need to adapt.",
            ],
            key_entities=["EU", "AI Act"],
            why_it_matters="It affects compliance planning.",
            confidence_note="High confidence.",
        )


class FakeFetcher:
    async def fetch(self, result: RankedSearchResult) -> ArticleContent:
        if result.title.endswith("one"):
            raise RuntimeError("fetch failed")
        return ArticleContent(
            url=result.url,
            title=result.title,
            text="This article body contains enough detail for a summary.",
            source=result.source,
            published_date=result.published_date,
        )


async def fake_rewriter(query: str, language: str) -> QueryRewritePlan:
    assert language == "en"
    return QueryRewritePlan(
        search_terms=["ai regulation latest news"],
        time_filter="week",
        language="en",
        topic="AI regulation",
    )


@pytest.mark.asyncio
async def test_pipeline_keeps_partial_results_when_one_article_fails() -> None:
    pipeline = NewsPipeline(
        rewriter=fake_rewriter,
        searxng_client=FakeSearxNGClient(),
        ollama_client=FakeOllamaClient(),
        ranker=SearchRanker(),
        fetcher=FakeFetcher(),
    )

    response = await pipeline.run(SummarizeRequest(query="Summarize AI regulation news", max_results=2, language="en"))

    assert response.rewritten_query.topic == "AI regulation"
    assert len(response.results) == 2
    assert all(item.summary is not None for item in response.results)
    assert all(item.error is None for item in response.results)
    assert all(item.url != "https://example.com/article-1" for item in response.results)
    assert [item.url for item in response.results] == [
        "https://example.com/article-2",
        "https://example.com/article-3",
    ]
