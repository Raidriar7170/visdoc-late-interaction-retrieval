"""Deterministic visual-smoke retrieval baselines for Phase 3A."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from visdoc_retrieve.data_schema import (
    QueryRecord,
    ValidationError,
    load_jsonl,
    validate_family_split_consistency,
    validate_pages,
    validate_queries,
)

TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
VECTOR_DIMENSIONS = 16
CHUNK_SIZE = 128


@dataclass(frozen=True, slots=True)
class VisualPage:
    """A page record with resolved image bytes for local smoke retrieval."""

    page_id: str
    split: str
    family_id: str
    image_bytes: bytes
    doc_id: str = ""
    page_number: int = 0
    image_path: str = ""
    text_path: str = ""


@dataclass(frozen=True, slots=True)
class VisualQuery:
    """A query record with split metadata and positive page IDs."""

    query_id: str
    query: str
    positive_page_ids: tuple[str, ...]
    split: str
    family_id: str
    query_type: str


@dataclass(frozen=True, slots=True)
class VisualCorpus:
    """Manifest-backed visual-smoke retrieval corpus."""

    pages: tuple[VisualPage, ...]
    queries: tuple[VisualQuery, ...]
    pages_by_id: Mapping[str, VisualPage]
    queries_by_id: Mapping[str, VisualQuery]


@dataclass(frozen=True, slots=True)
class RankingItem:
    """One ranked page result."""

    page_id: str
    score: float


@dataclass(frozen=True, slots=True)
class MockEmbeddingCache:
    """Serializable deterministic mock embedding cache evidence."""

    metadata: Mapping[str, object]
    query_embeddings: Mapping[str, tuple[tuple[float, ...], ...]]
    page_embeddings: Mapping[str, tuple[tuple[float, ...], ...]]


class VisualRetriever(Protocol):
    """Minimal visual retriever interface for MVP late-interaction scaffolds."""

    uses_external_model: bool
    gpu_required: bool

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

    def rank(self, query: VisualQuery) -> tuple[RankingItem, ...]:
        """Rank candidate pages for one visual query."""


def load_visual_corpus(
    *,
    repo_root: Path,
    pages_manifest: Path,
    queries_manifest: Path,
) -> VisualCorpus:
    """Load Phase 1 manifests and resolve page image artifacts."""

    pages = validate_pages(load_jsonl(_resolve_path(repo_root, pages_manifest)))
    queries = validate_queries(
        load_jsonl(_resolve_path(repo_root, queries_manifest)),
        pages,
    )
    validate_family_split_consistency(pages, queries)

    visual_pages: list[VisualPage] = []
    for page in pages:
        image_path = _resolve_repo_relative_path(repo_root, page.image_path)
        if not image_path.is_file():
            raise ValidationError(f"missing image artifact: {page.image_path}")
        visual_pages.append(
            VisualPage(
                page_id=page.page_id,
                split=page.split,
                family_id=page.family_id,
                image_bytes=image_path.read_bytes(),
                doc_id=page.doc_id,
                page_number=page.page_number,
                image_path=page.image_path,
                text_path=page.text_path,
            )
        )

    visual_queries = tuple(_visual_query(query) for query in queries)
    visual_pages_tuple = tuple(sorted(visual_pages, key=lambda page: page.page_id))
    return VisualCorpus(
        pages=visual_pages_tuple,
        queries=visual_queries,
        pages_by_id={page.page_id: page for page in visual_pages_tuple},
        queries_by_id={query.query_id: query for query in visual_queries},
    )


class VisualSmokeRetriever:
    """Local deterministic late-interaction-style visual smoke retriever."""

    uses_external_model = False
    gpu_required = False

    def __init__(self, pages: Sequence[VisualPage]) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._patch_tokens = {
            page.page_id: _image_patch_tokens(page.image_bytes) for page in self._pages
        }
        self._patch_vectors = {
            page_id: tuple(_vector_for_token(token) for token in tokens)
            for page_id, tokens in self._patch_tokens.items()
        }

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    @property
    def patch_token_counts(self) -> Mapping[str, int]:
        """Return the deterministic patch-token count per page."""

        return {
            page_id: len(tokens) for page_id, tokens in self._patch_tokens.items()
        }

    def rank(self, query: str) -> tuple[RankingItem, ...]:
        """Rank pages with a deterministic max-sim late-interaction score."""

        query_vectors = tuple(
            _vector_for_token(token) for token in _query_tokens(query)
        )
        scored = [
            RankingItem(
                page.page_id,
                _late_interaction_score(
                    query_vectors,
                    self._patch_vectors[page.page_id],
                ),
            )
            for page in self._pages
        ]
        return tuple(sorted(scored, key=lambda item: (-item.score, item.page_id)))


class MockVisualRetriever:
    """Deterministic CPU-only visual late-interaction mock retriever."""

    retriever_id = "mock_visual"
    uses_external_model = False
    gpu_required = False

    def __init__(self, pages: Sequence[VisualPage]) -> None:
        self._pages = tuple(sorted(pages, key=lambda page: page.page_id))
        self._page_embeddings = {
            page.page_id: self.embed_page(page) for page in self._pages
        }

    @property
    def index_size_pages(self) -> int:
        """Return the number of indexed pages."""

        return len(self._pages)

    @property
    def page_embeddings(self) -> Mapping[str, tuple[tuple[float, ...], ...]]:
        """Return deterministic page token embeddings keyed by page ID."""

        return self._page_embeddings

    def embed_query(self, query: VisualQuery) -> tuple[tuple[float, ...], ...]:
        """Embed query tokens deterministically for mock MaxSim scoring."""

        return tuple(_vector_for_token(token) for token in _query_tokens(query.query))

    def embed_page(self, page: VisualPage) -> tuple[tuple[float, ...], ...]:
        """Embed page patch tokens deterministically for mock MaxSim scoring."""

        return tuple(
            _vector_for_token(token) for token in _mock_page_tokens(page.image_bytes)
        )

    def rank(self, query: VisualQuery) -> tuple[RankingItem, ...]:
        """Rank pages with deterministic MaxSim and stable page-ID tie-breaking."""

        query_embeddings = self.embed_query(query)
        scored = [
            RankingItem(
                page.page_id,
                maxsim_score(
                    query_token_embeddings=query_embeddings,
                    page_token_embeddings=self._page_embeddings[page.page_id],
                ),
            )
            for page in self._pages
        ]
        return tuple(sorted(scored, key=lambda item: (-item.score, item.page_id)))


def maxsim_score(
    *,
    query_token_embeddings: Sequence[Sequence[float]],
    page_token_embeddings: Sequence[Sequence[float]],
) -> float:
    """Compute mean query-token MaxSim over page-token embeddings."""

    if not query_token_embeddings or not page_token_embeddings:
        return 0.0

    query_matrix = _validate_embedding_matrix(query_token_embeddings)
    page_matrix = _validate_embedding_matrix(page_token_embeddings)
    query_dimensions = len(query_matrix[0])
    page_dimensions = len(page_matrix[0])
    if query_dimensions != page_dimensions:
        raise ValidationError(
            "query and page token embeddings must use same dimensions"
        )

    token_scores = []
    for query_vector in query_matrix:
        token_scores.append(
            max(
                0.0,
                max(_dot(query_vector, page_vector) for page_vector in page_matrix),
            )
        )
    return sum(token_scores) / len(token_scores)


def build_mock_embedding_cache(
    retriever: MockVisualRetriever,
    queries: Sequence[VisualQuery],
) -> MockEmbeddingCache:
    """Build a deterministic mock visual embedding cache artifact."""

    query_embeddings = {
        query.query_id: retriever.embed_query(query)
        for query in sorted(queries, key=lambda item: item.query_id)
    }
    page_embeddings = {
        page_id: retriever.page_embeddings[page_id]
        for page_id in sorted(retriever.page_embeddings)
    }
    return MockEmbeddingCache(
        metadata={
            "schema_version": "mock_visual_embedding_cache/v1",
            "retriever_id": retriever.retriever_id,
            "provider": "deterministic_mock",
            "network_required": False,
            "gpu_required": False,
            "model_download_required": False,
            "external_embeddings_enabled": False,
            "embedding_dimensions": VECTOR_DIMENSIONS,
            "page_count": len(page_embeddings),
            "query_count": len(query_embeddings),
            "scoring": "maxsim_mean_query_token_best_page_token",
        },
        query_embeddings=query_embeddings,
        page_embeddings=page_embeddings,
    )


def write_mock_embedding_cache(path: Path, cache: MockEmbeddingCache) -> None:
    """Write mock visual embedding cache evidence as deterministic JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "metadata": dict(cache.metadata),
        "query_embeddings": cache.query_embeddings,
        "page_embeddings": cache.page_embeddings,
    }
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_mock_embedding_cache(path: Path) -> MockEmbeddingCache:
    """Load and validate deterministic mock visual embedding cache evidence."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("mock embedding cache must be a JSON object")
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise ValidationError("mock embedding cache metadata must be an object")
    return MockEmbeddingCache(
        metadata=cast(dict[str, object], metadata),
        query_embeddings=_embedding_map(data.get("query_embeddings"), "query"),
        page_embeddings=_embedding_map(data.get("page_embeddings"), "page"),
    )


def _visual_query(query: QueryRecord) -> VisualQuery:
    return VisualQuery(
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
        raise ValidationError(f"image_path escapes repo root: {path}") from exc
    return resolved


def _query_tokens(query: str) -> tuple[str, ...]:
    return tuple(match.group(0).lower() for match in TOKEN_PATTERN.finditer(query))


def _image_patch_tokens(image_bytes: bytes) -> tuple[str, ...]:
    text = image_bytes.decode("latin-1", errors="ignore")
    text_tokens = [
        f"text:{match.group(0).lower()}"
        for match in TOKEN_PATTERN.finditer(text)
        if match.group(0).strip()
    ]
    chunk_tokens = [
        f"chunk:{hashlib.sha256(chunk).hexdigest()[:16]}"
        for chunk in _chunks(image_bytes, CHUNK_SIZE)
    ]
    byte_length_token = f"bytes:{len(image_bytes)}"
    return tuple(text_tokens + chunk_tokens + [byte_length_token])


def _mock_page_tokens(image_bytes: bytes) -> tuple[str, ...]:
    text = image_bytes.decode("latin-1", errors="ignore")
    text_tokens = [
        f"text:{match.group(0).lower()}"
        for match in TOKEN_PATTERN.finditer(text)
        if match.group(0).strip()
    ][:64]
    chunk_tokens = [
        f"chunk:{hashlib.sha256(chunk).hexdigest()[:16]}"
        for chunk in _chunks(image_bytes, 4096)[:16]
    ]
    content_digest_token = f"digest:{hashlib.sha256(image_bytes).hexdigest()[:16]}"
    byte_length_token = f"bytes:{len(image_bytes)}"
    return tuple(text_tokens + chunk_tokens + [content_digest_token, byte_length_token])


def _chunks(data: bytes, size: int) -> tuple[bytes, ...]:
    if not data:
        return (b"",)
    return tuple(data[index : index + size] for index in range(0, len(data), size))


def _vector_for_token(token: str) -> tuple[float, ...]:
    if token.startswith("text:"):
        token = token.removeprefix("text:")
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    values = tuple((digest[index] / 127.5) - 1.0 for index in range(VECTOR_DIMENSIONS))
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return (0.0,) * VECTOR_DIMENSIONS
    return tuple(value / norm for value in values)


def _late_interaction_score(
    query_vectors: Sequence[Sequence[float]],
    patch_vectors: Sequence[Sequence[float]],
) -> float:
    return maxsim_score(
        query_token_embeddings=query_vectors,
        page_token_embeddings=patch_vectors,
    )


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


def _validate_embedding_matrix(
    embeddings: Sequence[Sequence[float]],
) -> tuple[tuple[float, ...], ...]:
    dimension: int | None = None
    matrix: list[tuple[float, ...]] = []
    for vector in embeddings:
        row = tuple(float(value) for value in vector)
        if not row:
            raise ValidationError("token embeddings must use same dimensions")
        if dimension is None:
            dimension = len(row)
        elif len(row) != dimension:
            raise ValidationError("token embeddings must use same dimensions")
        matrix.append(row)
    return tuple(matrix)


def _embedding_map(
    value: object,
    label: str,
) -> dict[str, tuple[tuple[float, ...], ...]]:
    if not isinstance(value, dict):
        raise ValidationError(f"mock embedding cache {label} embeddings must be object")
    embeddings: dict[str, tuple[tuple[float, ...], ...]] = {}
    for item_id, matrix in value.items():
        if not isinstance(item_id, str) or not item_id:
            raise ValidationError(f"mock embedding cache {label} IDs must be strings")
        if not isinstance(matrix, list):
            raise ValidationError(
                f"mock embedding cache {label} embedding must be a list"
            )
        embeddings[item_id] = _matrix_from_json(matrix, label)
    return embeddings


def _matrix_from_json(
    matrix: list[object],
    label: str,
) -> tuple[tuple[float, ...], ...]:
    rows: list[tuple[float, ...]] = []
    for row in matrix:
        if not isinstance(row, list):
            raise ValidationError(
                f"mock embedding cache {label} token embedding must be a list"
            )
        rows.append(tuple(float(value) for value in row))
    if rows:
        return _validate_embedding_matrix(rows)
    return ()
