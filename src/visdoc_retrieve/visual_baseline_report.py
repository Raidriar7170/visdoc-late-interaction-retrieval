"""Config-driven diagnostic reports for visual smoke baselines."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from visdoc_retrieve.retrieval_metrics import compute_retrieval_metrics
from visdoc_retrieve.visual_retrieval import (
    VisualSmokeRetriever,
    load_visual_corpus,
)


@dataclass(frozen=True, slots=True)
class VisualMethodConfig:
    """Config for one visual report method."""

    enabled: bool


@dataclass(frozen=True, slots=True)
class VisualReportConfig:
    """Committed config for a diagnostic visual smoke report."""

    name: str
    pages_manifest: Path
    queries_manifest: Path
    evaluated_splits: tuple[str, ...]
    final_test_split: str
    output_path: Path
    methods: dict[str, VisualMethodConfig]


def load_visual_report_config(path: Path) -> VisualReportConfig:
    """Load a JSON visual-baseline report config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("visual report config must be a JSON object")
    methods = {
        name: _method_config(value)
        for name, value in cast(dict[str, object], data["methods"]).items()
    }
    return VisualReportConfig(
        name=_required_str(data, "name"),
        pages_manifest=Path(_required_str(data, "pages_manifest")),
        queries_manifest=Path(_required_str(data, "queries_manifest")),
        evaluated_splits=tuple(cast(list[str], data["evaluated_splits"])),
        final_test_split=_required_str(data, "final_test_split"),
        output_path=Path(_required_str(data, "output_path")),
        methods=methods,
    )


def run_visual_baseline_report(
    config: VisualReportConfig,
    *,
    repo_root: Path,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Generate and persist a deterministic diagnostic visual smoke report."""

    if config.final_test_split in set(config.evaluated_splits):
        raise ValueError("final_test_split must not be included in evaluated_splits")

    corpus = load_visual_corpus(
        repo_root=repo_root,
        pages_manifest=config.pages_manifest,
        queries_manifest=config.queries_manifest,
    )
    pages = tuple(
        page for page in corpus.pages if page.split in set(config.evaluated_splits)
    )
    queries = tuple(
        query for query in corpus.queries if query.split in set(config.evaluated_splits)
    )
    positives = {
        query.query_id: query.positive_page_ids
        for query in sorted(queries, key=lambda item: item.query_id)
    }

    methods: dict[str, object] = {}
    if config.methods.get("visual_smoke", VisualMethodConfig(False)).enabled:
        methods["visual_smoke"] = _method_report(
            VisualSmokeRetriever(pages),
            queries,
            positives,
        )

    report: dict[str, object] = {
        "name": config.name,
        "status": "diagnostic_only",
        "visual_retriever_status": "deterministic_local_smoke",
        "corpus": {
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest": str(config.queries_manifest),
        },
        "evaluated_splits": list(config.evaluated_splits),
        "excluded_splits": [config.final_test_split],
        "final_test_status": "not_run",
        "methods": methods,
        "boundary": {
            "visual_smoke_only": True,
            "page_image_artifacts_read": True,
            "page_text_artifacts_read": False,
            "network_required": False,
            "gpu_required": False,
            "external_model_download_required": False,
            "colpali_or_colqwen_inference": False,
            "hard_negative_triples_emitted": False,
            "training_run": False,
            "final_test_evaluated": False,
            "benchmark_claim": "none",
        },
    }
    destination = repo_root / (output_path or config.output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for local visual report generation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_visual_report_config(args.config)
    run_visual_baseline_report(
        config,
        repo_root=args.repo_root,
        output_path=args.output,
    )
    return 0


def _method_report(
    retriever: VisualSmokeRetriever,
    queries: Sequence[Any],
    positives: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    rankings = {
        query.query_id: tuple(item.page_id for item in retriever.rank(query.query))
        for query in queries
    }
    metrics = compute_retrieval_metrics(rankings=rankings, positives=positives)
    return {
        "metrics": metrics.to_dict(),
        "diagnostics": {
            "latency_per_query_ms": {
                "label": "diagnostic",
                "status": "not_measured_deterministic_report",
                "value": None,
            },
            "index_size_pages": {
                "label": "diagnostic",
                "value": retriever.index_size_pages,
            },
            "patch_tokens_per_page": _patch_token_support(
                retriever.patch_token_counts
            ),
        },
        "hard_negative_hit_rate": {
            "status": "not_available",
            "support": 0,
        },
        "external_model_enabled": retriever.uses_external_model,
        "gpu_required": retriever.gpu_required,
    }


def _patch_token_support(counts: Mapping[str, int]) -> dict[str, int]:
    if not counts:
        return {"pages": 0, "min": 0, "max": 0}
    values = list(counts.values())
    return {"pages": len(values), "min": min(values), "max": max(values)}


def _method_config(value: object) -> VisualMethodConfig:
    if not isinstance(value, dict):
        raise ValueError("visual method config must be an object")
    return VisualMethodConfig(enabled=bool(value.get("enabled", False)))


def _required_str(data: dict[str, object], field: str) -> str:
    value = data[field]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
