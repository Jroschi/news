from __future__ import annotations

import httpx

from app.models.schemas import ArticleContent, RankedSearchResult
from app.services.extractor import ArticleExtractor


class ArticleFetcher:
    def __init__(self, http_client: httpx.AsyncClient, extractor: ArticleExtractor) -> None:
        self.http_client = http_client
        self.extractor = extractor

    async def fetch(self, result: RankedSearchResult) -> ArticleContent:
        response = await self.http_client.get(str(result.url), follow_redirects=True)
        response.raise_for_status()
        text = self.extractor.extract_text(response.text)
        if not text:
            raise ValueError("No readable article content extracted")
        return ArticleContent(
            url=result.url,
            title=result.title,
            text=text,
            source=result.source,
            published_date=result.published_date,
        )
