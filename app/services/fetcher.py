from __future__ import annotations

import httpx
import logging
import random
import time
from typing import Optional
from httpx import HTTPStatusError
from app.models.schemas import ArticleContent, RankedSearchResult
from app.services.extractor import ArticleExtractor
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleFetcher:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        extractor: ArticleExtractor,
        user_agents: Optional[list] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: float = 10.0
    ) -> None:
        self.http_client = http_client
        self.extractor = extractor
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    async def fetch(self, result: RankedSearchResult) -> ArticleContent:
        url = str(result.url)
        logger.info(f"Fetching article from: {url}")

        for attempt in range(self.max_retries + 1):
            try:
                # Randomly select a user agent
                headers = {"User-Agent": random.choice(self.user_agents)}
                response = await self.http_client.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )

                # Handle HTTP errors
                response.raise_for_status()

                # Extract content
                text = self.extractor.extract_text(response.text)
                if not text:
                    raise ValueError("No readable article content extracted")

                # Return success
                return ArticleContent(
                    url=result.url,
                    title=result.title,
                    text=text,
                    source=result.source,
                    published_date=result.published_date,
                )

            except HTTPStatusError as e:
                if e.response.status_code == 429:  # Too many requests
                    logger.warning(f"Rate limited (429) for {url}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                elif e.response.status_code in (403, 401):  # Forbidden/Unauthorized
                    logger.warning(f"Access denied (403/401) for {url}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Error fetching {url} (Attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise
