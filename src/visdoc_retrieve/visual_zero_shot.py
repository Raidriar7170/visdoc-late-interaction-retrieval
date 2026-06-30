"""Config loading and validation for optional visual zero-shot retrieval."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from visdoc_retrieve.data_schema import (
    ValidationError,
    load_jsonl,
    validate_family_split_consistency,
    validate_pages,
    validate_queries,
)


class VisualZeroShotConfigError(ValueError):
    """Raised when visual zero-shot config preflight fails."""


@dataclass(frozen=True, slots=True)
class VisualZeroShotBackendConfig:
    """Optional local visual-model backend settings."""

    name: str
    model_path: Path | None
    model_id: str | None
    device: str
    batch_size: int
    cache_path: Path
    local_files_only: bool


@dataclass(frozen=True, slots=True)
class VisualZeroShotOutputs:
    """Output paths for an optional visual zero-shot run."""

    metrics: Path
    rankings: Path
    run_card: Path


@dataclass(frozen=True, slots=True)
class VisualZeroShotConfig:
    """Top-level optional visual zero-shot config."""

    name: str
    backend: VisualZeroShotBackendConfig
    corpus_path: Path
    query_path: Path
    qrels_path: Path
    evaluated_splits: tuple[str, ...]
    candidate_universe: str
    final_test_split: str
    outputs: VisualZeroShotOutputs
    ci_required: bool

    @property
    def pages_manifest(self) -> Path:
        """Backward-compatible alias for the corpus page manifest path."""

        return self.corpus_path

    @property
    def queries_manifest(self) -> Path:
        """Backward-compatible alias for the query manifest path."""

        return self.query_path


def load_visual_zero_shot_config(path: Path) -> VisualZeroShotConfig:
    """Load a visual zero-shot JSON config without importing model runtimes."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VisualZeroShotConfigError("visual zero-shot config must be an object")
    backend_data = _required_mapping(data, "backend")
    outputs = _required_mapping(data, "outputs")
    return VisualZeroShotConfig(
        name=_required_str(data, "name"),
        ci_required=_optional_bool(data.get("ci_required", False), "ci_required"),
        corpus_path=Path(_required_str_alias(data, "corpus_path", "pages_manifest")),
        query_path=Path(_required_str_alias(data, "query_path", "queries_manifest")),
        qrels_path=Path(_required_str(data, "qrels_path")),
        evaluated_splits=tuple(_required_str_list(data, "evaluated_splits")),
        candidate_universe=_required_str(data, "candidate_universe"),
        final_test_split=_required_str(data, "final_test_split"),
        backend=VisualZeroShotBackendConfig(
            name=_required_str(backend_data, "name"),
            model_path=_optional_path(backend_data.get("model_path")),
            model_id=_optional_str(backend_data.get("model_id")),
            device=_required_str(backend_data, "device"),
            batch_size=_positive_int(backend_data.get("batch_size"), "batch_size"),
            cache_path=Path(_required_str(backend_data, "cache_path")),
            local_files_only=_optional_bool(
                backend_data.get("local_files_only", True),
                "local_files_only",
            ),
        ),
        outputs=VisualZeroShotOutputs(
            metrics=Path(_required_str(outputs, "metrics")),
            rankings=Path(_required_str(outputs, "rankings")),
            run_card=Path(_required_str(outputs, "run_card")),
        ),
    )


def check_visual_zero_shot_config(
    config: VisualZeroShotConfig,
    *,
    repo_root: Path,
) -> None:
    """Validate local paths and policy without loading optional runtimes."""

    if config.backend.name != "local_visual_model":
        raise VisualZeroShotConfigError(
            f"unsupported visual zero-shot backend: {config.backend.name}"
        )
    if config.backend.model_path is None and not config.backend.model_id:
        raise VisualZeroShotConfigError(
            "local visual backend requires model_path or model_id"
        )
    if config.backend.model_path is not None:
        model_path = _resolve_path(repo_root, config.backend.model_path)
        if not model_path.exists():
            raise VisualZeroShotConfigError(
                f"local model path does not exist: {config.backend.model_path}"
            )
    if not config.backend.local_files_only:
        raise VisualZeroShotConfigError(
            "visual zero-shot backend must use local_files_only=true"
        )
    if config.final_test_split in set(config.evaluated_splits):
        raise VisualZeroShotConfigError(
            "final_test_split must not be included in evaluated_splits"
        )
    if config.candidate_universe != "evaluated_split_pages":
        raise VisualZeroShotConfigError(
            "visual zero-shot currently supports candidate_universe="
            "evaluated_split_pages"
        )

    pages_path = _require_existing_file(repo_root, config.corpus_path, "corpus")
    queries_path = _require_existing_file(repo_root, config.query_path, "query")
    qrels_path = _require_existing_file(repo_root, config.qrels_path, "qrels")
    try:
        pages = validate_pages(load_jsonl(pages_path))
        queries = validate_queries(load_jsonl(queries_path), pages)
        validate_family_split_consistency(pages, queries)
        qrels = validate_queries(load_jsonl(qrels_path), pages)
    except ValidationError as exc:
        raise VisualZeroShotConfigError(
            f"qrels/query validation failed: {exc}"
        ) from exc
    if not qrels:
        raise VisualZeroShotConfigError("qrels path must contain at least one record")
    query_positive_ids = {
        query.query_id: query.positive_page_ids for query in queries
    }
    qrels_positive_ids = {
        query.query_id: query.positive_page_ids for query in qrels
    }
    if qrels_positive_ids != query_positive_ids:
        raise VisualZeroShotConfigError(
            "qrels path must match query relevance IDs and positive pages"
        )


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _require_existing_file(repo_root: Path, path: Path, label: str) -> Path:
    resolved = _resolve_path(repo_root, path)
    if not resolved.is_file():
        raise VisualZeroShotConfigError(f"{label} path does not exist: {path}")
    return resolved


def _required_mapping(data: Mapping[str, object], key: str) -> dict[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise VisualZeroShotConfigError(f"{key} must be an object")
    return cast(dict[str, object], value)


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise VisualZeroShotConfigError(f"{key} must be a non-empty string")
    return value


def _required_str_alias(data: Mapping[str, object], key: str, fallback: str) -> str:
    value = data.get(key)
    if value is None:
        value = data.get(fallback)
    if not isinstance(value, str) or not value.strip():
        raise VisualZeroShotConfigError(
            f"{key} must be a non-empty string"
        )
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise VisualZeroShotConfigError("optional string value must be non-empty")
    return value


def _optional_bool(value: object, key: str) -> bool:
    if not isinstance(value, bool):
        raise VisualZeroShotConfigError(f"{key} must be a boolean")
    return value


def _optional_path(value: object) -> Path | None:
    string_value = _optional_str(value)
    return None if string_value is None else Path(string_value)


def _required_str_list(data: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise VisualZeroShotConfigError(f"{key} must be a non-empty list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise VisualZeroShotConfigError(f"{key} must contain strings")
        items.append(item)
    return tuple(items)


def _positive_int(value: object, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise VisualZeroShotConfigError(f"{key} must be a positive integer")
    return value
