import httpx
import pytest

from app.clients.ollama import OllamaClient
from app.services.query_rewriter import QueryRewriterService


@pytest.mark.asyncio
async def test_query_rewriter_parses_structured_json_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        return httpx.Response(
            200,
            json={
                "response": '{"search_terms":["latest ai regulation news","eu ai act updates"],"time_filter":"week","language":"en","topic":"AI regulation"}'
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://ollama.test") as client:
        ollama = OllamaClient(
            base_url="http://ollama.test",
            chat_model="test-model",
            embedding_model="embed-model",
            http_client=client,
        )
        service = QueryRewriterService(ollama)
        plan = await service.rewrite("Summarize AI regulation news this week")

    assert plan.language == "en"
    assert plan.time_filter == "week"
    assert plan.search_terms == ["latest ai regulation news", "eu ai act updates"]
