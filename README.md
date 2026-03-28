# News Summarizer API

Turn a plain-English news question into concise, structured article summaries.

This project is for people who want to ask one question (for example, “What changed this week in EU AI policy?”) and quickly get:
- the most relevant recent articles,
- short bullet-point summaries,
- key entities,
- and a quick “why this matters” takeaway.

## What you can do

- Ask in natural English (no special query syntax needed).
- Get 3–5 ranked news results per request.
- Receive a consistent response format that is easy to plug into apps, dashboards, or automations.
- Keep getting partial results even if one article fails to fetch or summarize.

## How it works (high level)

When you send a request, the API:
1. Rewrites your question into better news search terms.
2. Finds candidate articles.
3. Ranks them for relevance.
4. Extracts article text.
5. Returns a structured summary for each article.

You only call one endpoint; the pipeline runs behind the scenes.

## API endpoints

### `GET /health`
Simple health check.

Example response:

```json
{ "status": "ok" }
```

### `POST /summarize`
Main endpoint for news summarization.

Request body:

```json
{
  "query": "Summarize the latest EU AI regulation news",
  "max_results": 3,
  "language": "en"
}
```

Request notes:
- `query` (required): your news question in English.
- `max_results` (optional): number of summaries to return, from **3 to 5**.
- `language` (optional): currently supports only `"en"`.

Example response:

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

## Quick start

### Option 1: Run with Docker Compose (recommended)

```bash
docker compose up --build
```

Then call the API at `http://localhost:8000`.

### Option 2: Run locally for development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Try it with curl

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were the biggest AI regulation updates this week?",
    "max_results": 3,
    "language": "en"
  }'
```

## Running tests

```bash
pytest
```

## Good to know

- This service is optimized for English-language news requests.
- Responses are designed to be readable by humans and reliable for downstream apps.
- If one article cannot be processed, the request can still succeed with other results.
