from __future__ import annotations

from app.clients.ollama import OllamaClient
from app.models.schemas import QueryRewritePlan


class QueryRewriterService:
    def __init__(self, ollama_client: OllamaClient) -> None:
        self.ollama_client = ollama_client

    async def rewrite(self, query: str, language: str = "en") -> QueryRewritePlan:
        if language != "en":
            raise ValueError("Only English requests are supported")
        plan = await self.ollama_client.rewrite_query(query)
        if plan.language != "en":
            raise ValueError("Query rewrite returned a non-English search plan")
        return plan
