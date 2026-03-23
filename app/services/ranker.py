from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from app.models.schemas import QueryRewritePlan, RankedSearchResult, SearchResult


class SearchRanker:
    def rank(
        self,
        query: str,
        rewrite_plan: QueryRewritePlan,
        results: list[SearchResult],
        embeddings: list[list[float]] | None,
        max_results: int,
    ) -> list[RankedSearchResult]:
        if not results:
            return []
        if embeddings and len(embeddings) == len(results) + 1:
            return self._rank_with_embeddings(query, rewrite_plan, results, embeddings, max_results)
        return self._rank_with_heuristics(query, rewrite_plan, results, max_results)

    def _rank_with_embeddings(
        self,
        query: str,
        rewrite_plan: QueryRewritePlan,
        results: list[SearchResult],
        embeddings: list[list[float]],
        max_results: int,
    ) -> list[RankedSearchResult]:
        query_vector = embeddings[0]
        scored: list[RankedSearchResult] = []
        for result, vector in zip(results, embeddings[1:], strict=True):
            score = self._cosine_similarity(query_vector, vector)
            bonus = self._heuristic_bonus(query, rewrite_plan, result)
            final_score = max(0.0, score + bonus)
            scored.append(
                RankedSearchResult(
                    **result.model_dump(),
                    score=round(final_score, 4),
                    ranking_reason="embedding_similarity+keyword_bonus",
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:max_results]

    def _rank_with_heuristics(
        self,
        query: str,
        rewrite_plan: QueryRewritePlan,
        results: list[SearchResult],
        max_results: int,
    ) -> list[RankedSearchResult]:
        scored: list[RankedSearchResult] = []
        for result in results:
            score = self._heuristic_bonus(query, rewrite_plan, result)
            scored.append(
                RankedSearchResult(
                    **result.model_dump(),
                    score=round(max(score, 0.0), 4),
                    ranking_reason="keyword_overlap_heuristic",
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:max_results]

    def _heuristic_bonus(self, query: str, rewrite_plan: QueryRewritePlan, result: SearchResult) -> float:
        query_tokens = self._tokenize(query)
        term_tokens = self._tokenize(" ".join(rewrite_plan.search_terms))
        combined_tokens = query_tokens + term_tokens
        if not combined_tokens:
            return 0.0
        result_tokens = self._tokenize(f"{result.title} {result.snippet} {result.source or ''}")
        overlap = Counter(result_tokens) & Counter(combined_tokens)
        raw_overlap = sum(overlap.values())
        title_hits = sum(token in self._tokenize(result.title) for token in set(combined_tokens))
        recency_bonus = 0.1 if result.published_date else 0.0
        return (raw_overlap / max(len(set(combined_tokens)), 1)) + (0.05 * title_hits) + recency_bonus

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if len(token) > 2]
