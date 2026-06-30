"""Import-safe scaffold for optional local visual zero-shot backends."""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from visdoc_retrieve.data_schema import ValidationError
from visdoc_retrieve.visual_zero_shot import VisualZeroShotBackendConfig

VISUAL_EMBEDDING_CACHE_SCHEMA = "visual_token_embedding_cache/v1"


class VisualZeroShotBackendError(RuntimeError):
    """Raised when optional real visual backend execution cannot proceed."""


@dataclass(frozen=True, slots=True)
class VisualEmbeddingCache:
    """Generic query/page token embedding cache for MaxSim scoring."""

    metadata: Mapping[str, object]
    query_embeddings: Mapping[str, tuple[tuple[float, ...], ...]]
    page_embeddings: Mapping[str, tuple[tuple[float, ...], ...]]


class LocalVisualModelBackend:
    """Lazy local-model backend boundary.

    This class intentionally performs no heavyweight imports during module
    import, construction, config checks, or dry-run preflight.
    """

    uses_external_model = True

    def __init__(self, config: VisualZeroShotBackendConfig) -> None:
        self.config = config

    @property
    def gpu_required(self) -> bool:
        """Return whether the explicit device names a CUDA backend."""

        return self.config.device.startswith("cuda")

    def run(self) -> None:
        """Attempt a real local run, failing before any success artifact exists."""

        self._ensure_runtime_available()
        raise VisualZeroShotBackendError(
            "local visual model execution scaffold is present, but concrete "
            "ColPali/ColQwen inference is not implemented in this checkpoint"
        )

    def _ensure_runtime_available(self) -> None:
        if importlib.util.find_spec("colpali_engine") is None:
            raise VisualZeroShotBackendError(
                "optional runtime colpali_engine is not installed; install a "
                "local visual-model runtime and rerun without network downloads"
            )


def write_visual_embedding_cache(path: Path, cache: VisualEmbeddingCache) -> None:
    """Write a validated visual token embedding cache as deterministic JSON."""

    _validate_cache(cache)
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


def load_visual_embedding_cache(path: Path) -> VisualEmbeddingCache:
    """Load and validate a visual token embedding cache."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("visual embedding cache must be a JSON object")
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise ValidationError("visual embedding cache metadata must be an object")
    cache = VisualEmbeddingCache(
        metadata=cast(dict[str, object], metadata),
        query_embeddings=_embedding_map(data.get("query_embeddings"), "query"),
        page_embeddings=_embedding_map(data.get("page_embeddings"), "page"),
    )
    _validate_cache(cache)
    return cache


def _validate_cache(cache: VisualEmbeddingCache) -> None:
    expected_dimensions = cache.metadata.get("embedding_dimensions")
    if (
        not isinstance(expected_dimensions, int)
        or isinstance(expected_dimensions, bool)
        or expected_dimensions < 1
    ):
        raise ValidationError("embedding_dimensions must be a positive integer")
    schema_version = cache.metadata.get("schema_version")
    if schema_version != VISUAL_EMBEDDING_CACHE_SCHEMA:
        raise ValidationError(
            f"schema_version must be {VISUAL_EMBEDDING_CACHE_SCHEMA}"
        )
    for key in ("backend_name", "provider", "model_reference"):
        value = cache.metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{key} must be a non-empty string")
    query_count = cache.metadata.get("query_count")
    if (
        not isinstance(query_count, int)
        or isinstance(query_count, bool)
        or query_count != len(cache.query_embeddings)
    ):
        raise ValidationError("query_count must match query embeddings")
    page_count = cache.metadata.get("page_count")
    if (
        not isinstance(page_count, int)
        or isinstance(page_count, bool)
        or page_count != len(cache.page_embeddings)
    ):
        raise ValidationError("page_count must match page embeddings")
    for label, embeddings in (
        ("query", cache.query_embeddings),
        ("page", cache.page_embeddings),
    ):
        for item_id, matrix in embeddings.items():
            if not item_id:
                raise ValidationError(f"{label} embedding ID must be non-empty")
            _validate_matrix(matrix, expected_dimensions)


def _embedding_map(
    value: object,
    label: str,
) -> dict[str, tuple[tuple[float, ...], ...]]:
    if not isinstance(value, dict):
        raise ValidationError(
            f"visual embedding cache {label} embeddings must be object"
        )
    embeddings: dict[str, tuple[tuple[float, ...], ...]] = {}
    for item_id, matrix in value.items():
        if not isinstance(item_id, str) or not item_id:
            raise ValidationError(f"visual embedding cache {label} IDs must be strings")
        if not isinstance(matrix, list):
            raise ValidationError(
                f"visual embedding cache {label} embedding must be a list"
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
                f"visual embedding cache {label} token embedding must be a list"
            )
        try:
            rows.append(tuple(float(value) for value in row))
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"visual embedding cache {label} token embeddings must be numeric"
            ) from exc
    return tuple(rows)


def _validate_matrix(
    matrix: Sequence[Sequence[float]],
    expected_dimensions: int,
) -> None:
    for row in matrix:
        try:
            values = tuple(float(value) for value in row)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "visual embedding cache token embeddings must be numeric"
            ) from exc
        if len(values) != expected_dimensions:
            raise ValidationError("token embeddings must use same dimensions")
