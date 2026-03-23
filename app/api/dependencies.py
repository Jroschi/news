from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from fastapi import Depends

from app.clients.ollama import OllamaClient
from app.clients.searxng import SearxNGClient
from app.core.config import settings
from app.services.extractor import ArticleExtractor
from app.services.fetcher import ArticleFetcher
from app.services.pipeline import NewsPipeline
from app.services.query_rewriter import QueryRewriterService
from app.services.ranker import SearchRanker


async def get_http_client() -> AsyncIterator[httpx.AsyncClient]:
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


def get_pipeline(http_client: httpx.AsyncClient = Depends(get_http_client)) -> NewsPipeline:
    ollama_client = OllamaClient(
        base_url=settings.ollama_url,
        chat_model=settings.ollama_chat_model,
        embedding_model=settings.ollama_embedding_model,
        http_client=http_client,
    )
    searxng_client = SearxNGClient(base_url=settings.searxng_url, http_client=http_client)
    extractor = ArticleExtractor(max_characters=settings.max_article_characters)
    fetcher = ArticleFetcher(http_client=http_client, extractor=extractor)
    rewriter = QueryRewriterService(ollama_client)
    return NewsPipeline(
        rewriter=rewriter.rewrite,
        searxng_client=searxng_client,
        ollama_client=ollama_client,
        ranker=SearchRanker(),
        fetcher=fetcher,
        search_limit=settings.default_search_limit,
    )
