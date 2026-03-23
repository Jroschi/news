from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SummarizeRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language news request.")
    max_results: int = Field(default=3, ge=3, le=5)
    language: Literal["en"] = Field(default="en")


class QueryRewritePlan(BaseModel):
    search_terms: list[str] = Field(..., min_length=1, max_length=6)
    time_filter: str | None = Field(default=None)
    language: Literal["en"] = Field(default="en")
    topic: str = Field(..., min_length=1)

    @field_validator("search_terms")
    @classmethod
    def strip_terms(cls, search_terms: list[str]) -> list[str]:
        cleaned = [term.strip() for term in search_terms if term.strip()]
        if not cleaned:
            raise ValueError("At least one search term is required.")
        return cleaned


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""
    source: str | None = None
    published_date: str | None = None
    engine: str | None = None


class RankedSearchResult(SearchResult):
    score: float = Field(..., ge=0.0)
    ranking_reason: str


class ArticleContent(BaseModel):
    url: HttpUrl
    title: str
    text: str = Field(..., min_length=1)
    source: str | None = None
    published_date: str | None = None


class ArticleSummary(BaseModel):
    summary: list[str] = Field(..., min_length=1)
    key_entities: list[str] = Field(default_factory=list)
    why_it_matters: str
    confidence_note: str


class ArticleSummaryResult(BaseModel):
    title: str
    url: HttpUrl
    source: str | None = None
    published_date: str | None = None
    score: float = Field(..., ge=0.0)
    ranking_reason: str
    content_preview: str = ""
    summary: ArticleSummary | None = None
    error: str | None = None


class SummarizeResponse(BaseModel):
    query: str
    rewritten_query: QueryRewritePlan
    results: list[ArticleSummaryResult]
