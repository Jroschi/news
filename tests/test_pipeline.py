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
        ]


class FakeOllamaClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0], [0.9, 0.1], [0.8, 0.2]]

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
        if result.title.endswith("two"):
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

    response = await pipeline.run(SummarizeRequest(query="Summarize AI regulation news", max_results=3, language="en"))

    assert response.rewritten_query.topic == "AI regulation"
    assert len(response.results) == 2
    assert response.results[0].summary is not None
    assert response.results[1].summary is None
    assert response.results[1].error == "fetch failed"
