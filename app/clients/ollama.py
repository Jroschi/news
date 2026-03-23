from __future__ import annotations

import json
from typing import Any

import httpx

from app.models.schemas import ArticleSummary, QueryRewritePlan


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embedding_model: str, http_client: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.http_client = http_client

    async def rewrite_query(self, user_query: str) -> QueryRewritePlan:
        prompt = (
            "You rewrite an English-only news request into a JSON search plan. "
            "Return compact JSON with keys search_terms, time_filter, language, and topic. "
            "language must be 'en'. search_terms must be an array of 1 to 6 concise search queries. "
            "Do not include markdown or explanation. User query: "
            f"{user_query}"
        )
        payload = {
            "model": self.chat_model,
            "prompt": prompt,
            "stream": False,
            "format": QueryRewritePlan.model_json_schema(),
        }
        response = await self.http_client.post(f"{self.base_url}/api/generate", json=payload)
        response.raise_for_status()
        body = response.json()
        content = self._extract_text(body)
        return QueryRewritePlan.model_validate_json(content)

    async def summarize_article(self, article_title: str, article_text: str) -> ArticleSummary:
        prompt = (
            "Summarize this English news article as JSON. Return keys summary, key_entities, why_it_matters, confidence_note. "
            "summary must be an array of 3 to 6 bullet-style strings. Do not include markdown fences. "
            f"Title: {article_title}\nArticle:\n{article_text}"
        )
        payload = {
            "model": self.chat_model,
            "prompt": prompt,
            "stream": False,
            "format": ArticleSummary.model_json_schema(),
        }
        response = await self.http_client.post(f"{self.base_url}/api/generate", json=payload)
        response.raise_for_status()
        body = response.json()
        content = self._extract_text(body)
        return ArticleSummary.model_validate_json(content)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            payload = {"model": self.embedding_model, "input": text}
            response = await self.http_client.post(f"{self.base_url}/api/embed", json=payload)
            response.raise_for_status()
            body = response.json()
            vector = body.get("embeddings") or body.get("embedding")
            if isinstance(vector, list) and vector and isinstance(vector[0], list):
                embeddings.append([float(item) for item in vector[0]])
            elif isinstance(vector, list):
                embeddings.append([float(item) for item in vector])
            else:
                raise ValueError("Ollama embedding response was missing embedding data")
        return embeddings

    @staticmethod
    def _extract_text(body: dict[str, Any]) -> str:
        raw = body.get("response") or body.get("message", {}).get("content")
        if raw is None:
            raise ValueError(f"Unexpected Ollama response: {json.dumps(body)}")
        return str(raw).strip()
