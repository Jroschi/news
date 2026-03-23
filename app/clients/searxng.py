from __future__ import annotations

import httpx

from app.models.schemas import SearchResult


class SearxNGClient:
    def __init__(self, base_url: str, http_client: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client

    async def search(self, query: str, language: str = "en", limit: int = 10) -> list[SearchResult]:
        response = await self.http_client.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "language": language,
                "format": "json",
                "categories": "news",
            },
        )
        response.raise_for_status()
        body = response.json()
        return self._normalize_results(body, limit)

    @staticmethod
    def _normalize_results(payload: dict, limit: int) -> list[SearchResult]:
        normalized: list[SearchResult] = []
        for item in payload.get("results", []):
            url = item.get("url")
            title = (item.get("title") or "").strip()
            if not url or not title:
                continue
            normalized.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=(item.get("content") or item.get("snippet") or "").strip(),
                    source=item.get("source") or item.get("engines", [None])[0],
                    published_date=item.get("publishedDate") or item.get("published_date"),
                    engine=(item.get("engines") or [None])[0],
                )
            )
            if len(normalized) >= limit:
                break
        return normalized
