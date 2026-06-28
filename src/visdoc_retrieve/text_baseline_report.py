"""Config-driven diagnostic reports for text retrieval baselines."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from visdoc_retrieve.retrieval_metrics import compute_retrieval_metrics
from visdoc_retrieve.text_retrieval import (
    BM25Retriever,
    DenseTextRetriever,
    HybridRetriever,
    load_text_corpus,
)


@dataclass(frozen=True, slots=True)
class MethodConfig:
    """Config for one report method."""

    enabled: bool
    external_embeddings_enabled: bool = False
    rrf_k: int = 60


@dataclass(frozen=True, slots=True)
class ReportConfig:
    """Committed config for a diagnostic text baseline report."""

    name: str
    pages_manifest: Path
    queries_manifest: Path
    evaluated_splits: tuple[str, ...]
    final_test_split: str
    output_path: Path
    methods: dict[str, MethodConfig]


def load_report_config(path: Path) -> ReportConfig:
    """Load a JSON text-baseline report config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report config must be a JSON object")
    methods = {
        name: _method_config(value)
        for name, value in cast(dict[str, object], data["methods"]).items()
    }
    return ReportConfig(
        name=_required_str(data, "name"),
        pages_manifest=Path(_required_str(data, "pages_manifest")),
        queries_manifest=Path(_required_str(data, "queries_manifest")),
        evaluated_splits=tuple(cast(list[str], data["evaluated_splits"])),
        final_test_split=_required_str(data, "final_test_split"),
        output_path=Path(_required_str(data, "output_path")),
        methods=methods,
    )


def run_text_baseline_report(
    config: ReportConfig,
    *,
    repo_root: Path,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Generate and persist a deterministic diagnostic text-baseline report."""

    if config.final_test_split in set(config.evaluated_splits):
        raise ValueError("final_test_split must not be included in evaluated_splits")

    corpus = load_text_corpus(
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
    if config.methods.get("bm25", MethodConfig(False)).enabled:
        methods["bm25"] = _method_report(BM25Retriever(pages), queries, positives)
    if config.methods.get("dense_text", MethodConfig(False)).enabled:
        methods["dense_text"] = _method_report(
            DenseTextRetriever(pages),
            queries,
            positives,
            external_embeddings_enabled=config.methods[
                "dense_text"
            ].external_embeddings_enabled,
        )
    if config.methods.get("hybrid_rrf", MethodConfig(False)).enabled:
        methods["hybrid_rrf"] = _method_report(
            HybridRetriever(pages, rrf_k=config.methods["hybrid_rrf"].rrf_k),
            queries,
            positives,
        )

    report: dict[str, object] = {
        "name": config.name,
        "status": "diagnostic_only",
        "corpus": {
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest": str(config.queries_manifest),
        },
        "evaluated_splits": list(config.evaluated_splits),
        "excluded_splits": [config.final_test_split],
        "final_test_status": "not_run",
        "methods": methods,
        "boundary": {
            "text_only": True,
            "network_required": False,
            "gpu_required": False,
            "external_embedding_paths_enabled_by_default": False,
            "hard_negative_triples_emitted": False,
            "visual_retrieval_run": False,
            "training_run": False,
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
    """CLI entry point for local report generation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_report_config(args.config)
    run_text_baseline_report(config, repo_root=args.repo_root, output_path=args.output)
    return 0


def _method_report(
    retriever: BM25Retriever | DenseTextRetriever | HybridRetriever,
    queries: Sequence[Any],
    positives: dict[str, tuple[str, ...]],
    *,
    external_embeddings_enabled: bool = False,
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
            "ranked_page_support": _ranked_page_support(rankings),
        },
        "hard_negative_hit_rate": {
            "status": "not_available",
            "support": 0,
        },
        "external_embeddings_enabled": external_embeddings_enabled,
    }


def _ranked_page_support(rankings: dict[str, tuple[str, ...]]) -> dict[str, int]:
    if not rankings:
        return {"queries": 0, "min_pages": 0, "max_pages": 0}
    counts = [len(ranking) for ranking in rankings.values()]
    return {
        "queries": len(rankings),
        "min_pages": min(counts),
        "max_pages": max(counts),
    }


def _method_config(value: object) -> MethodConfig:
    if not isinstance(value, dict):
        raise ValueError("method config must be an object")
    external = cast(dict[str, object], value.get("external_embeddings", {}))
    return MethodConfig(
        enabled=bool(value.get("enabled", False)),
        external_embeddings_enabled=bool(external.get("enabled", False)),
        rrf_k=int(value.get("rrf_k", 60)),
    )


def _required_str(data: dict[str, object], field: str) -> str:
    value = data[field]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
