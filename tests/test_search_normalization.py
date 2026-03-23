from app.clients.searxng import SearxNGClient


def test_searxng_normalizes_and_filters_results() -> None:
    payload = {
        "results": [
            {
                "title": " Useful title ",
                "url": "https://example.com/a",
                "content": "Snippet A",
                "source": "Example",
                "publishedDate": "2026-03-20",
                "engines": ["news"]
            },
            {"title": "", "url": "https://example.com/b"},
            {"title": "No URL"},
        ]
    }

    results = SearxNGClient._normalize_results(payload, limit=10)

    assert len(results) == 1
    assert results[0].title == "Useful title"
    assert str(results[0].url) == "https://example.com/a"
    assert results[0].snippet == "Snippet A"
