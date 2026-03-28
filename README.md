# News summarization backend

FastAPI backend that rewrites an English news query into a structured search plan, queries SearxNG, ranks candidate articles with Ollama embeddings or a heuristic fallback, fetches and cleans article HTML with BeautifulSoup, summarizes each article independently with Ollama, and returns JSON. Designed primarily for personal use with middleware MCP server

## Features

- English-only `POST /summarize` API.
- Structured query rewrite and article summary schemas with Pydantic.
- Async `httpx` integration for Ollama, SearxNG, and article fetching.
- Resilient pipeline: one failed article fetch or summary does not fail the whole request.
- Dockerfile and `docker-compose.yml` for the API, Ollama, and SearxNG.
- Spoof dependency API in `app/testing/spoof_api.py` for offline or isolated testing.

## Request shape

```json
{
  "query": "Summarize the latest EU AI regulation news",
  "max_results": 3,
  "language": "en"
}
```

## Response shape

```json
{
  "query": "Summarize the latest EU AI regulation news",
  "rewritten_query": {
    "search_terms": ["eu ai regulation latest news", "eu ai act updates"],
    "time_filter": "week",
    "language": "en",
    "topic": "AI regulation"
  },
  "results": [
    {
      "title": "Example article",
      "url": "https://example.com/article",
      "source": "Example News",
      "published_date": "2026-03-22",
      "score": 0.92,
      "ranking_reason": "embedding_similarity+keyword_bonus",
      "content_preview": "...",
      "summary": {
        "summary": ["..."],
        "key_entities": ["EU", "AI Act"],
        "why_it_matters": "...",
        "confidence_note": "..."
      },
      "error": null
    }
  ]
}
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

## Running with Docker Compose

```bash
docker compose up --build
```
