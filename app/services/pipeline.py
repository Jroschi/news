from __future__ import annotations
from typing import Awaitable, Callable

from app.clients.ollama import OllamaClient
from app.clients.searxng import SearxNGClient
from app.models.schemas import ArticleSummaryResult, QueryRewritePlan, SummarizeRequest, SummarizeResponse
from app.services.fetcher import ArticleFetcher
from app.services.ranker import SearchRanker


class NewsPipeline:
    def __init__(
        self,
        rewriter: Callable[[str, str], Awaitable[QueryRewritePlan]],
        searxng_client: SearxNGClient,
        ollama_client: OllamaClient,
        ranker: SearchRanker,
        fetcher: ArticleFetcher,
        search_limit: int = 10,
    ) -> None:
        self.rewriter = rewriter
        self.searxng_client = searxng_client
        self.ollama_client = ollama_client
        self.ranker = ranker
        self.fetcher = fetcher
        self.search_limit = search_limit

    async def run(self, request: SummarizeRequest) -> SummarizeResponse:
        rewrite_plan = await self.rewriter(request.query, request.language)
        search_results = await self._search_all_terms(rewrite_plan)

        embeddings = await self._safe_embed(
            [request.query] + [f"{result.title}\n{result.snippet}" for result in search_results]
        )
        ranked_results = self.ranker.rank(
            query=request.query,
            rewrite_plan=rewrite_plan,
            results=search_results,
            embeddings=embeddings,
            max_results=len(search_results),
        )
        successful_results = []
        for candidate in ranked_results:
            if len(successful_results) == request.max_results:
                break
            summary_result = await self._summarize_result(candidate)
            if summary_result.summary is None or summary_result.error:
                continue
            successful_results.append(summary_result)
        return SummarizeResponse(query=request.query, rewritten_query=rewrite_plan, results=successful_results)

    async def _search_all_terms(self, rewrite_plan: QueryRewritePlan):
        collected = []
        seen_urls = set()
        for term in rewrite_plan.search_terms:
            term_results = await self.searxng_client.search(term, language=rewrite_plan.language, limit=self.search_limit)
            for item in term_results:
                if str(item.url) in seen_urls:
                    continue
                seen_urls.add(str(item.url))
                collected.append(item)
        return collected

    async def _safe_embed(self, texts: list[str]) -> list[list[float]] | None:
        try:
            return await self.ollama_client.embed_texts(texts)
        except Exception:
            return None

    async def _summarize_result(self, result) -> ArticleSummaryResult:
        try:
            article = await self.fetcher.fetch(result)
            summary = await self.ollama_client.summarize_article(article.title, article.text)
            return ArticleSummaryResult(
                title=result.title,
                url=result.url,
                source=result.source,
                published_date=result.published_date,
                score=result.score,
                ranking_reason=result.ranking_reason,
                content_preview=article.text[:280],
                summary=summary,
            )
        except Exception as exc:
            return ArticleSummaryResult(
                title=result.title,
                url=result.url,
                source=result.source,
                published_date=result.published_date,
                score=result.score,
                ranking_reason=result.ranking_reason,
                content_preview="",
                summary=None,
                error=str(exc),
            )
