from __future__ import annotations

from fastapi import FastAPI, Query

app = FastAPI(title="Spoof news dependencies")


@app.post("/ollama/api/generate")
async def ollama_generate(payload: dict) -> dict:
    prompt = payload.get("prompt", "")
    if "search plan" in prompt:
        return {
            "response": '{"search_terms":["ai regulation latest news","eu ai act updates"],"time_filter":"week","language":"en","topic":"AI regulation"}'
        }
    return {
        "response": '{"summary":["Policy updates advanced this week.","Regulators focused on compliance duties.","Companies are preparing implementation steps."],"key_entities":["EU","AI Act"],"why_it_matters":"The change affects AI compliance planning.","confidence_note":"High confidence from the provided article text."}'
    }


@app.post("/ollama/api/embed")
async def ollama_embed(payload: dict) -> dict:
    text = payload.get("input", "")
    base = float(len(text.split()) or 1)
    return {"embeddings": [[base, base / 2, 1.0]]}


@app.get("/searxng/search")
async def searxng_search(q: str = Query(...), format: str = Query("json"), **_: str) -> dict:
    return {
        "query": q,
        "results": [
            {
                "title": "AI policy update",
                "url": "https://example.com/article-1",
                "content": "A fresh policy development in AI regulation.",
                "source": "Example News",
                "publishedDate": "2026-03-22",
                "engines": ["news"]
            },
            {
                "title": "Market reaction to AI rules",
                "url": "https://example.com/article-2",
                "content": "Companies respond to the latest AI rules.",
                "source": "Example Market",
                "publishedDate": "2026-03-21",
                "engines": ["news"]
            }
        ],
    }


@app.get("/article/{slug}")
async def article(slug: str) -> str:
    return f"<html><body><article><p>{slug} lead paragraph with enough words for extraction testing.</p><p>Second paragraph adds article detail and context for summarization.</p></article></body></html>"
