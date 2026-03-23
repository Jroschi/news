Goal

Turn a natural-language user request into a ranked set of relevant news articles, fetch and clean the article text, summarize each result, and return the summaries.

Proposed architecture
1) API / Orchestrator service

A small backend service that coordinates the whole pipeline.

Responsibilities:

accept the user query
call Ollama to rewrite the query into search terms
query SearxNG
rank results with embeddings or a reranker
fetch the full article pages
clean the article text
send each article to the summarizer LLM
return structured results to the caller
2) Ollama service

Used for query rewriting and final summarization.

Suggested split:

query-to-search model: small, fast instruct model
summarization model: better instruction-following model with enough context window
3) SearxNG service

Search engine aggregator running in Docker on port 8081.

Used twice:

first, for search results and snippets
second, optionally for resolving/opening article URLs if you want to keep all network access behind one service pattern
4) Ranking / embedding service

This can be:

a local embedding model such as mxbai-embed-large, or
a reranker model for better precision

Best practice:

use embeddings for coarse filtering
use reranking for the final top 3–5 items
5) Fetch-and-clean worker

A worker component that:

downloads the article HTML
extracts main content with BeautifulSoup
removes nav bars, cookie banners, scripts, ads, and boilerplate
normalizes text for the LLM
End-to-end request flow
User sends query
Example: “Summarize the most important AI regulation news from this week.”
Query rewriting
Ollama converts that into actionable search terms, for example:
AI regulation latest week
artificial intelligence policy news
EU AI law recent developments
Search via SearxNG
The orchestrator sends the rewritten terms to SearxNG and gets:
titles
snippets
URLs
source metadata
Ranking
Each result is embedded, compared against the user intent/query, and ranked.
Keep top 3–5.
Article fetch
For each selected URL:
download HTML
parse with BeautifulSoup
extract main text
discard irrelevant sections
Article summarization
Send each cleaned article to Ollama with a summarization prompt.
Return a per-article summary plus optional metadata:
title
source
published date if available
summary
relevance score
Final response
The orchestrator returns a JSON payload or rendered UI result.
Recommended pipeline design
Query rewriting prompt

Have Ollama output structured JSON, not free text.

Example output:

{
  "search_terms": [
    "AI regulation latest news",
    "EU AI Act recent updates",
    "artificial intelligence policy developments"
  ],
  "time_filter": "week",
  "language": "en",
  "topic": "AI regulation"
}

This makes downstream processing deterministic.

Ranking strategy

Use a two-stage approach:

Stage 1: embeddings to filter from many search hits to maybe 10
Stage 2: reranker or similarity scoring to select final 3–5

If you only use embeddings, it will work, but the precision may be weaker than a reranker.

Article extraction

BeautifulSoup alone is okay for a first version, but raw BS4 often captures too much boilerplate.

A practical extraction flow:

remove script, style, noscript
prefer article, main, or content containers
fall back to paragraph density heuristics
join paragraphs into clean text
enforce a max character limit before summarization
Summarization prompt

Ask the model to produce:

3–6 bullet summary
key entities
why it matters
confidence/quality note if the article was thin or inaccessible

For news, this format is usually more useful than a generic paragraph.

Suggested Docker Compose layout
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - ollama
      - searxng
    environment:
      - SEARXNG_URL=http://searxng:8081
      - OLLAMA_URL=http://ollama:11434

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8081:8080"
    environment:
      - SEARXNG_BASE_URL=http://localhost:8081

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  worker:
    build: ./worker
    depends_on:
      - api
      - ollama
      - searxng

volumes:
  ollama_data:

You can also merge api and worker into one service for a simpler first version.

API shape

A simple request/response contract:

Request
{
  "query": "Summarize the latest EU AI regulation news",
  "max_results": 5,
  "language": "en"
}
Response
{
  "query": "Summarize the latest EU AI regulation news",
  "rewritten_search_terms": [
    "EU AI regulation latest news",
    "EU AI Act recent developments"
  ],
  "results": [
    {
      "title": "…",
      "url": "…",
      "source": "…",
      "summary": "…",
      "score": 0.92
    }
  ]
}
Important implementation choices
1) Make everything JSON-first

Have the LLM output JSON wherever possible:

query rewrite
article summary
final response structure

That reduces parsing errors.

2) Add caching

Cache:

search results by query
fetched article HTML by URL
final summaries by URL + model version

This avoids repeating expensive work.

3) Add timeouts and fallbacks

News sites often fail or block requests.

Recommended behavior:

timeout per fetch
retry once
if article text extraction fails, summarize snippet only
if one article fails, continue with the rest
4) Preserve provenance

Always keep:

source URL
title
snippet
fetch time
model version used

That makes debugging and trust much easier.

5) Optional deduplication

Search engines often return the same story from multiple mirrors.
Use URL canonicalization and similarity checks to remove duplicates.

Good first implementation stack
Backend: FastAPI
Queue/worker: Celery or a simple async worker
Search: SearxNG
LLM: Ollama
Embedding/ranking: mxbai-embed-large or a reranker
Extraction: BeautifulSoup + readability-style heuristics
Storage: SQLite or Postgres, depending on scale

For a first version, FastAPI + async tasks is enough.

One improvement I would strongly recommend

Use the embedding model only as the retrieval filter, not the final judge.

In practice:

embeddings are great for “find relevant”
rerankers are better for “which 3–5 are actually best”

That usually improves relevance a lot for news search.

Questions to confirm
Do you want the app to return only summaries, or also a grouped digest like “top stories by topic”?
Should it support multiple languages, or just English at first?
Do you want this as a pure backend API, or also a web UI in the same Docker stack?

I can turn this into a concrete system design, a folder structure, or a Docker Compose + FastAPI skeleton next.

1. Just summaries for now. 2) English only 3) Pure backend API in its own docker container to be called by other services. Next I would you to generate optimized for Codex design so the agent can get to implementing  it in codex.
Thought for a couple of seconds

Below is a Codex-optimized implementation design: narrow, deterministic, and organized so an agent can build it module by module without guessing.

News summarizer API — implementation spec
Product scope

A pure backend API that:

accepts a natural-language news query,
rewrites it into search terms with Ollama,
searches SearxNG,
ranks search results with embeddings/reranking,
fetches and cleans article pages,
summarizes each selected article,
returns only summaries plus provenance metadata.

English only. No UI. No topic clustering. No persistence required in v1 except optional caching.

Recommended stack

Use Python with:

FastAPI for the API
httpx for outbound HTTP
pydantic v2 for schema validation
BeautifulSoup4 for HTML cleaning
lxml parser if available
sentence-transformers or Ollama embedding endpoint for ranking
Ollama for query rewriting and summarization
SearxNG for search

Keep the implementation async where possible.

Non-goals

Do not implement in v1:

authentication
user accounts
frontend
topic clustering
long-term article storage
streaming responses
multilingual support
web scraping beyond the selected article URLs
Core pipeline
Request flow
API receives query.
LLM rewrites query into a structured search plan.
Search SearxNG with one or more generated search terms.
Deduplicate results.
Rank candidates with embeddings / reranker.
Select top 3–5 results.
Fetch each URL.
Extract readable article text.
Summarize each article independently.
Return summaries and metadata.
Important design rule

Every stage should produce structured data. Avoid passing raw LLM text into later steps unless it is validated.

API contract
Endpoint

POST /v1/summarize

Request body
{
  "query": "Summarize the latest EU AI regulation news",
  "max_results": 5
}
Response body
{
  "query": "Summarize the latest EU AI regulation news",
  "rewritten_query": {
    "search_terms": [
      "EU AI regulation latest news",
      "EU AI Act recent developments"
    ],
    "filters": {
      "language": "en",
      "recency_days": 14
    }
  },
  "results": [
    {
      "title": "Article title",
      "url": "https://example.com/article",
      "source": "example.com",
      "score": 0.93,
      "summary": [
        "First summary point.",
        "Second summary point.",
        "Third summary point."
      ],
      "fetched_at": "2026-03-23T12:34:56Z"
    }
  ]
}
Response behavior
Return at most max_results results.
If fewer than 3 high-quality results exist, return fewer rather than forcing noisy matches.
If article fetching fails, preserve the search result entry and include an error field for that item.
Internal service boundaries

Build the code around these modules:

app/api/

FastAPI routes and request/response models.

app/services/query_rewrite.py

Calls Ollama to turn the natural-language query into structured search terms.

app/services/search.py

Calls SearxNG and normalizes results.

app/services/ranking.py

Computes similarity scores and chooses the best results.

app/services/fetch.py

Fetches the article HTML from URLs.

app/services/extract.py

Cleans HTML and extracts main article text.

app/services/summarize.py

Calls Ollama to summarize a single article.

app/core/config.py

Loads environment variables.

app/core/http.py

Shared httpx.AsyncClient creation and timeout settings.

app/models/

Pydantic schemas for inputs, outputs, and intermediate objects.

tests/

Unit tests for each stage, plus one pipeline integration test using mocks.

Data models

Define these clearly and keep them stable.

SearchPlan

Fields:

search_terms: list[str]
language: str = "en"
recency_days: int | None
topic: str | None
SearchResult

Fields:

title: str
url: str
snippet: str | None
source: str | None
published_date: str | None
score: float | None
ArticleDocument

Fields:

url: str
title: str
text: str
source: str | None
published_date: str | None
ArticleSummary

Fields:

title: str
url: str
source: str | None
score: float
summary: list[str]
fetched_at: datetime
error: str | None = None
SummarizeRequest

Fields:

query: str
max_results: int = 5
SummarizeResponse

Fields:

query: str
rewritten_query: SearchPlan
results: list[ArticleSummary]
Query rewrite design

Use Ollama to produce JSON only.

Prompt requirements

The model must return:

search terms optimized for news search
recency hints
no commentary
valid JSON
Example output
{
  "search_terms": [
    "EU AI Act latest news",
    "European Union AI regulation update",
    "AI regulation Europe 2026"
  ],
  "language": "en",
  "recency_days": 14,
  "topic": "EU AI regulation"
}
Failure handling

If JSON parsing fails:

fallback to a simple heuristic split of the original query into 1–3 search terms,
continue the pipeline.

Do not fail the whole request just because query rewriting failed.

Search design
SearxNG usage

Use the SearxNG JSON endpoint and normalize fields into SearchResult.

Search with all rewritten terms, then merge results.

Deduplication

Deduplicate by:

normalized URL
canonical URL if available
title similarity
Search result merging

Combine results from multiple terms and keep the best snippet/title source.

Ranking design

Use a two-step ranking strategy.

Step 1: candidate filtering

Use embeddings or cosine similarity between:

user query
result title + snippet

Keep the top 10–15 candidates.

Step 2: final selection

Pick top 3–5.

Suggested scoring formula

final_score = 0.7 * semantic_similarity + 0.3 * snippet_match_bonus

Keep the formula simple and inspectable.

Ranking fallback

If embeddings are unavailable:

rank by title/snippet keyword overlap
favor recent results if a published date exists
Fetching and extraction design
Fetch rules

Use httpx with:

per-request timeout
redirect following enabled
a normal browser-like User-Agent
one retry max
Extraction rules

Use BeautifulSoup with these steps:

remove script, style, noscript, svg, iframe
prefer article, main, or [role=main]
if absent, gather paragraphs with sufficient text length
strip boilerplate text
normalize whitespace
drop empty lines
cap text length before summarization
Extraction fallback

If extraction fails:

fall back to concatenating paragraph text
if that also fails, summarize the snippet only
Summarization design

Summarize each article independently.

Output format

A short list of 3–6 bullet points. Keep it factual and news-style.

Prompt constraints

Tell the model:

only summarize the supplied article text
do not invent facts
keep the result compact
mention uncertainty if the article is thin or partial
do not include a headline rewrite unless requested
Recommended prompt structure

Input:

article title
source
cleaned article text
user query

Output:

bullet summary list
optional “why it matters” only if the article supports it
Error handling rules

The service must be resilient. A single bad URL must not fail the whole request.

Per-item failure behavior

If one article fetch or summarization fails:

keep the item in the response
include error
continue processing the rest
Request-level failure behavior

Only fail the request if:

query rewriting fails completely and fallback is impossible
search returns nothing usable
all candidate items fail
Recommended HTTP status codes
200 for successful response
422 for invalid request body
502 for upstream service failure when no usable output can be produced
504 for timeouts if the whole request exceeds the budget
Time budget

Design for a bounded request time.

Suggested limits:

query rewrite: 5s
search: 8s
ranking: 2s
fetch per article: 8s
summarize per article: 10s

Use concurrency, but cap parallel fetches/summaries to avoid overload.

Concurrency model

Use asyncio.

Suggested structure:

rewrite query
search all terms concurrently
dedupe and rank
fetch top candidates concurrently with a small semaphore, e.g. 3 at once
summarize fetched articles concurrently with a small semaphore, e.g. 2 at once

This keeps latency reasonable and avoids hammering news sites.

Environment variables

Define these in .env and validate on startup:

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_QUERY_MODEL=...
OLLAMA_SUMMARY_MODEL=...
OLLAMA_EMBED_MODEL=...
SEARXNG_BASE_URL=http://searxng:8081
HTTP_TIMEOUT_SECONDS=10
MAX_RESULTS_DEFAULT=5
USER_AGENT=...
Docker layout
Service 1: API

FastAPI app, main exposed service.

Service 2: Ollama

Used by the API container, not exposed externally unless needed for debugging.

Service 3: SearxNG

Search backend on port 8081.

Suggested repo layout
news-summarizer/
  app/
    main.py
    api/
      routes.py
    core/
      config.py
      http.py
    models/
      request.py
      response.py
      search.py
      article.py
    services/
      query_rewrite.py
      search.py
      ranking.py
      fetch.py
      extract.py
      summarize.py
      pipeline.py
    utils/
      text.py
      urls.py
  tests/
    test_query_rewrite.py
    test_search.py
    test_ranking.py
    test_extract.py
    test_pipeline.py
  Dockerfile
  docker-compose.yml
  pyproject.toml
  README.md
Implementation order for Codex

Build in this order:

project scaffold
config loading
request/response models
SearxNG client
Ollama query rewrite client
article fetcher
HTML extractor
article summarizer client
ranking module
pipeline orchestration
API route
tests
Dockerfile and compose

That order minimizes integration churn.

Acceptance criteria

The implementation is done when:

POST /v1/summarize accepts a JSON query
the service rewrites the query into structured search terms
SearxNG results are fetched and normalized
top results are ranked and selected
article pages are downloaded and cleaned
each article is summarized separately
the response returns summaries with URLs and scores
failures in one article do not break the entire request
the app runs in Docker and talks to Ollama and SearxNG by service name
