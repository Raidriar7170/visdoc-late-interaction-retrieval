"""Deterministic visual-smoke retrieval baselines for Phase 3A."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

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
    if not query_vectors or not patch_vectors:
        return 0.0
    token_scores = []
    for query_vector in query_vectors:
        token_scores.append(
            max(0.0, max(_dot(query_vector, patch) for patch in patch_vectors))
        )
    return sum(token_scores) / len(token_scores)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )
