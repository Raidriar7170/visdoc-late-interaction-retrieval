"""Deterministic text-only retrieval baselines for Phase 2."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import blake2b
from pathlib import Path
from typing import Protocol

from visdoc_retrieve.data_schema import (
    QueryRecord,
    ValidationError,
    load_jsonl,
    validate_family_split_consistency,
    validate_pages,
    validate_queries,
)

TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class TextPage:
    """A page record with resolved OCR-like text content."""

    page_id: str
    split: str
    family_id: str
    text: str
    doc_id: str = ""
    page_number: int = 0
    text_path: str = ""


@dataclass(frozen=True, slots=True)
class TextQuery:
    """A query record with split metadata and positive page IDs."""

    query_id: str
    query: str
    positive_page_ids: tuple[str, ...]
    split: str
    family_id: str
    query_type: str


@dataclass(frozen=True, slots=True)
class TextCorpus:
    """Manifest-backed text retrieval corpus."""

    pages: tuple[TextPage, ...]
    queries: tuple[TextQuery, ...]
    pages_by_id: Mapping[str, TextPage]
    queries_by_id: Mapping[str, TextQuery]


@dataclass(frozen=True, slots=True)
class RankingItem:
    """One ranked page result."""

    page_id: str
    score: float


class EmbeddingProvider(Protocol):
    """Minimal embedding-provider contract for config-gated neural text smoke."""

    @property
    def status(self) -> dict[str, object]:
        """Return provider provenance and local/external execution flags."""

    def embed(self, text: str) -> tuple[float, ...]:
        """Embed text deterministically for ranking."""


def load_text_corpus(
    *,
    repo_root: Path,
    pages_manifest: Path,
    queries_manifest: Path,
) -> TextCorpus:
    """Load Phase 1 manifests and resolve page text artifacts."""

    pages = validate_pages(load_jsonl(_resolve_path(repo_root, pages_manifest)))
    queries = validate_queries(
        load_jsonl(_resolve_path(repo_root, queries_manifest)),
        pages,
    )
    validate_family_split_consistency(pages, queries)

    text_pages: list[TextPage] = []
    for page in pages:
        text_path = _resolve_repo_relative_path(repo_root, page.text_path)
        if not text_path.is_file():
            raise ValidationError(f"missing text artifact: {page.text_path}")
        text_pages.append(
            TextPage(
                page_id=page.page_id,
                split=page.split,
                family_id=page.family_id,
                text=text_path.read_text(encoding="utf-8"),
                doc_id=page.doc_id,
                page_number=page.page_number,
                text_path=page.text_path,
            )
        )

    text_queries = tuple(_text_query(query) for query in queries)
    text_pages_tuple = tuple(sorted(text_pages, key=lambda page: page.page_id))
    return TextCorpus(
        pages=text_pages_tuple,
        queries=text_queries,
        pages_by_id={page.page_id: page for page in text_pages_tuple},
        queries_by_id={query.query_id: query for query in text_queries},
    )


def tokenize(text: str) -> tuple[str, ...]:
    """Tokenize text deterministically for all local baselines."""

    return tuple(match.group(0).lower() for match in TOKEN_PATTERN.finditer(text))


class BM25Retriever:
    """Small internal BM25 retriever with page-ID tie-breaking."""

    def __init__(
        self,
        pages: Sequence[TextPage],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._k1 = k1
        self._b = b
        self._doc_tokens = {page.page_id: tokenize(page.text) for page in self._pages}
        self._doc_lengths = {
            page_id: len(tokens) for page_id, tokens in self._doc_tokens.items()
        }
        self._avgdl = (
            sum(self._doc_lengths.values()) / len(self._doc_lengths)
            if self._doc_lengths
            else 0.0
        )
        self._term_frequencies = {
            page_id: Counter(tokens) for page_id, tokens in self._doc_tokens.items()
        }
        self._document_frequencies = self._build_document_frequencies()

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank all indexed pages for a query."""

        query_tokens = tokenize(query)
        scored = [
            RankingItem(page.page_id, self._score_page(page.page_id, query_tokens))
            for page in self._pages
        ]
        return tuple(sorted(scored, key=lambda item: (-item.score, item.page_id)))

    def _build_document_frequencies(self) -> dict[str, int]:
        frequencies: dict[str, int] = {}
        for tokens in self._doc_tokens.values():
            for token in set(tokens):
                frequencies[token] = frequencies.get(token, 0) + 1
        return frequencies

    def _score_page(self, page_id: str, query_tokens: Sequence[str]) -> float:
        if not self._pages or not query_tokens:
            return 0.0
        score = 0.0
        page_length = self._doc_lengths[page_id]
        term_frequency = self._term_frequencies[page_id]
        for token in query_tokens:
            frequency = term_frequency[token]
            if frequency == 0:
                continue
            document_frequency = self._document_frequencies.get(token, 0)
            idf = math.log(
                1 + (len(self._pages) - document_frequency + 0.5)
                / (document_frequency + 0.5)
            )
            denominator = frequency + self._k1 * (
                1 - self._b + self._b * page_length / self._avgdl
            )
            score += idf * frequency * (self._k1 + 1) / denominator
        return score


class LexicalCosineRetriever:
    """Deterministic local lexical-vector cosine baseline."""

    method_id = "lexical_cosine"
    uses_external_embeddings = False

    def __init__(self, pages: Sequence[TextPage]) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._vectors = {
            page.page_id: _normalized_counter(tokenize(page.text))
            for page in self._pages
        }

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank all indexed pages with deterministic cosine similarity."""

        query_vector = _normalized_counter(tokenize(query))
        scored = [
            RankingItem(page.page_id, _dot(query_vector, self._vectors[page.page_id]))
            for page in self._pages
        ]
        return tuple(sorted(scored, key=lambda item: (-item.score, item.page_id)))


class LocalStubEmbeddingProvider:
    """Deterministic local embedding provider for neural-text validation."""

    def __init__(self, *, dimensions: int = 32) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions

    @property
    def status(self) -> dict[str, object]:
        """Return explicit non-external provider status for reports."""

        return {
            "provider": "local_stub",
            "status": "mock_or_local_stub",
            "external_embeddings_enabled": False,
            "network_required": False,
            "gpu_required": False,
            "model_download_required": False,
            "embedding_cache_required": False,
        }

    def embed(self, text: str) -> tuple[float, ...]:
        """Hash tokens into a deterministic normalized vector."""

        vector = [0.0] * self._dimensions
        for token in tokenize(text):
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        return _normalized_vector(vector)


class NeuralTextRetriever:
    """Config-gated neural text retriever backed by an embedding provider."""

    method_id = "neural_text"

    def __init__(
        self,
        pages: Sequence[TextPage],
        *,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._provider = provider or LocalStubEmbeddingProvider()
        self._vectors = {
            page.page_id: self._provider.embed(page.text) for page in self._pages
        }

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    @property
    def uses_external_embeddings(self) -> bool:
        """Return whether the configured provider uses external embeddings."""

        return bool(self._provider.status["external_embeddings_enabled"])

    @property
    def provider_status(self) -> dict[str, object]:
        """Return provider provenance and execution flags."""

        return self._provider.status

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank all indexed pages with provider embeddings."""

        query_vector = self._provider.embed(query)
        scored = [
            RankingItem(
                page.page_id,
                _vector_dot(query_vector, self._vectors[page.page_id]),
            )
            for page in self._pages
        ]
        return tuple(sorted(scored, key=lambda item: (-item.score, item.page_id)))


class BM25LexicalRrfRetriever:
    """BM25 plus lexical-cosine reciprocal-rank fusion."""

    method_id = "bm25_lexical_rrf"

    def __init__(
        self,
        pages: Sequence[TextPage],
        *,
        rrf_k: int = 60,
        bm25_rankings: Mapping[str, Sequence[str]] | None = None,
        lexical_rankings: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._page_ids = tuple(page.page_id for page in self._pages)
        self._rrf_k = rrf_k
        self._bm25_rankings = bm25_rankings
        self._lexical_rankings = lexical_rankings
        self._bm25 = BM25Retriever(self._pages) if bm25_rankings is None else None
        self._lexical = (
            LexicalCosineRetriever(self._pages) if lexical_rankings is None else None
        )

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank pages by reciprocal rank fusion."""

        sparse = self._ranking_for(query, self._bm25_rankings, self._bm25)
        lexical = self._ranking_for(query, self._lexical_rankings, self._lexical)
        return _rrf_rank(self._page_ids, (sparse, lexical), self._rrf_k)

    @staticmethod
    def _ranking_for(
        query: str,
        injected_rankings: Mapping[str, Sequence[str]] | None,
        retriever: BM25Retriever | LexicalCosineRetriever | None,
    ) -> tuple[str, ...]:
        if injected_rankings is not None:
            return tuple(injected_rankings[query])
        if retriever is None:
            return ()
        return tuple(item.page_id for item in retriever.rank(query))


class BM25NeuralRrfRetriever:
    """BM25 plus neural-text reciprocal-rank fusion."""

    method_id = "bm25_neural_rrf"

    def __init__(
        self,
        pages: Sequence[TextPage],
        *,
        provider: EmbeddingProvider | None = None,
        rrf_k: int = 60,
        bm25_rankings: Mapping[str, Sequence[str]] | None = None,
        neural_rankings: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._page_ids = tuple(page.page_id for page in self._pages)
        self._rrf_k = rrf_k
        self._bm25_rankings = bm25_rankings
        self._neural_rankings = neural_rankings
        self._bm25 = BM25Retriever(self._pages) if bm25_rankings is None else None
        self._neural = (
            NeuralTextRetriever(self._pages, provider=provider)
            if neural_rankings is None
            else None
        )

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    @property
    def provider_status(self) -> dict[str, object]:
        """Return neural provider status when rankings are computed locally."""

        if self._neural is None:
            return LocalStubEmbeddingProvider().status
        return self._neural.provider_status

    @property
    def uses_external_embeddings(self) -> bool:
        """Return whether the neural side uses external embeddings."""

        return bool(self.provider_status["external_embeddings_enabled"])

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank pages by reciprocal rank fusion."""

        sparse = self._ranking_for(query, self._bm25_rankings, self._bm25)
        neural = self._ranking_for(query, self._neural_rankings, self._neural)
        return _rrf_rank(self._page_ids, (sparse, neural), self._rrf_k)

    @staticmethod
    def _ranking_for(
        query: str,
        injected_rankings: Mapping[str, Sequence[str]] | None,
        retriever: BM25Retriever | NeuralTextRetriever | None,
    ) -> tuple[str, ...]:
        if injected_rankings is not None:
            return tuple(injected_rankings[query])
        if retriever is None:
            return ()
        return tuple(item.page_id for item in retriever.rank(query))


def _text_query(query: QueryRecord) -> TextQuery:
    return TextQuery(
        query_id=query.query_id,
        query=query.query,
        positive_page_ids=query.positive_page_ids,
        split=query.split,
        family_id=query.family_id,
        query_type=query.query_type,
    )


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _resolve_repo_relative_path(repo_root: Path, path: str) -> Path:
    resolved = repo_root / path
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValidationError(f"text_path escapes repo root: {path}") from exc
    return resolved


def _normalized_counter(tokens: Sequence[str]) -> dict[str, float]:
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}
    return {token: value / norm for token, value in counts.items()}


def _dot(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _normalized_vector(values: Sequence[float]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return tuple(0.0 for _ in values)
    return tuple(value / norm for value in values)


def _vector_dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


def _rrf_rank(
    page_ids: Sequence[str],
    rankings: Sequence[Sequence[str]],
    rrf_k: int,
) -> tuple[RankingItem, ...]:
    scores = {page_id: 0.0 for page_id in page_ids}
    for ranking in rankings:
        for rank_index, page_id in enumerate(ranking, start=1):
            scores[page_id] = scores.get(page_id, 0.0) + 1 / (rrf_k + rank_index)
    return tuple(
        RankingItem(page_id, score)
        for page_id, score in sorted(
            scores.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )
