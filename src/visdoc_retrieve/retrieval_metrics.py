"""Retrieval metric computation for page-level rankings."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    """Aggregate page-retrieval metrics for one evaluated query set."""

    evaluated_queries: int
    ranked_pages_per_query: int
    recall_at_1: float
    recall_at_5: float
    mrr: float
    ndcg_at_10: float

    def to_dict(self) -> dict[str, int | float]:
        """Return a JSON-serializable metric dictionary."""

        return asdict(self)


def compute_retrieval_metrics(
    *,
    rankings: Mapping[str, Sequence[str]],
    positives: Mapping[str, Sequence[str]],
) -> RetrievalMetrics:
    """Compute deterministic Recall@1, Recall@5, MRR, and NDCG@10."""

    if not positives:
        return RetrievalMetrics(
            evaluated_queries=0,
            ranked_pages_per_query=0,
            recall_at_1=0.0,
            recall_at_5=0.0,
            mrr=0.0,
            ndcg_at_10=0.0,
        )

    recall_at_1 = 0.0
    recall_at_5 = 0.0
    reciprocal_rank = 0.0
    ndcg_at_10 = 0.0
    ranked_counts: list[int] = []

    for query_id in sorted(positives):
        ranking = tuple(rankings.get(query_id, ()))
        relevant = set(positives[query_id])
        ranked_counts.append(len(ranking))
        recall_at_1 += _recall_at(ranking, relevant, 1)
        recall_at_5 += _recall_at(ranking, relevant, 5)
        reciprocal_rank += _reciprocal_rank(ranking, relevant)
        ndcg_at_10 += _ndcg(ranking, relevant, 10)

    count = len(positives)
    return RetrievalMetrics(
        evaluated_queries=count,
        ranked_pages_per_query=min(ranked_counts) if ranked_counts else 0,
        recall_at_1=recall_at_1 / count,
        recall_at_5=recall_at_5 / count,
        mrr=reciprocal_rank / count,
        ndcg_at_10=ndcg_at_10 / count,
    )


def _recall_at(ranking: Sequence[str], relevant: set[str], limit: int) -> float:
    if not relevant:
        return 0.0
    hits = len(set(ranking[:limit]) & relevant)
    return hits / len(relevant)


def _reciprocal_rank(ranking: Sequence[str], relevant: set[str]) -> float:
    for rank_index, page_id in enumerate(ranking, start=1):
        if page_id in relevant:
            return 1 / rank_index
    return 0.0


def _ndcg(ranking: Sequence[str], relevant: set[str], limit: int) -> float:
    dcg = 0.0
    for rank_index, page_id in enumerate(ranking[:limit], start=1):
        if page_id in relevant:
            dcg += 1 / math.log2(rank_index + 1)
    ideal_hits = min(len(relevant), limit)
    ideal_dcg = sum(1 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    if ideal_dcg == 0:
        return 0.0
    return dcg / ideal_dcg
