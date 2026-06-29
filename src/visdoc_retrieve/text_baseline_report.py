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
    BM25LexicalRrfRetriever,
    BM25NeuralRrfRetriever,
    BM25Retriever,
    LexicalCosineRetriever,
    LocalStubEmbeddingProvider,
    NeuralTextRetriever,
    TextCorpus,
    TextPage,
    load_text_corpus,
)


@dataclass(frozen=True, slots=True)
class MethodConfig:
    """Config for one report method."""

    enabled: bool
    external_embeddings_enabled: bool = False
    provider: str = "local_stub"
    rrf_k: int = 60


@dataclass(frozen=True, slots=True)
class ReportConfig:
    """Committed config for a diagnostic text baseline report."""

    name: str
    pages_manifest: Path
    queries_manifest: Path
    evaluated_splits: tuple[str, ...]
    candidate_universe: str
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
        candidate_universe=str(
            data.get("candidate_universe", "evaluated_split_pages")
        ),
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
    queries = tuple(
        query for query in corpus.queries if query.split in set(config.evaluated_splits)
    )
    pages = _candidate_pages(corpus, config)
    positives = {
        query.query_id: query.positive_page_ids
        for query in sorted(queries, key=lambda item: item.query_id)
    }
    candidate_universe = _candidate_universe_report(config, pages, queries)

    methods: dict[str, object] = {}
    if config.methods.get("bm25", MethodConfig(False)).enabled:
        methods["bm25"] = _method_report(BM25Retriever(pages), queries, positives)
    if config.methods.get("lexical_cosine", MethodConfig(False)).enabled:
        methods["lexical_cosine"] = _method_report(
            LexicalCosineRetriever(pages),
            queries,
            positives,
        )
    neural_config = config.methods.get("neural_text", MethodConfig(False))
    neural_enabled = neural_config.enabled
    if neural_enabled:
        neural = NeuralTextRetriever(
            pages,
            provider=_embedding_provider(neural_config),
        )
        methods["neural_text"] = _method_report(
            neural,
            queries,
            positives,
            external_embeddings_enabled=neural.uses_external_embeddings,
            provider_status=neural.provider_status,
        )
    if config.methods.get("bm25_lexical_rrf", MethodConfig(False)).enabled:
        lexical_hybrid_config = config.methods["bm25_lexical_rrf"]
        methods["bm25_lexical_rrf"] = _method_report(
            BM25LexicalRrfRetriever(pages, rrf_k=lexical_hybrid_config.rrf_k),
            queries,
            positives,
            fusion={
                "sparse_side_method": "bm25",
                "dense_side_method": "lexical_cosine",
                "rrf_k": lexical_hybrid_config.rrf_k,
            },
        )
    if (
        neural_enabled
        and config.methods.get("bm25_neural_rrf", MethodConfig(False)).enabled
    ):
        neural_hybrid_config = config.methods["bm25_neural_rrf"]
        neural_hybrid = BM25NeuralRrfRetriever(
            pages,
            provider=_embedding_provider(neural_config),
            rrf_k=neural_hybrid_config.rrf_k,
        )
        methods["bm25_neural_rrf"] = _method_report(
            neural_hybrid,
            queries,
            positives,
            external_embeddings_enabled=neural_hybrid.uses_external_embeddings,
            provider_status=neural_hybrid.provider_status,
            fusion={
                "sparse_side_method": "bm25",
                "dense_side_method": "neural_text",
                "rrf_k": neural_hybrid_config.rrf_k,
            },
        )

    report: dict[str, object] = {
        "name": config.name,
        "status": "diagnostic_only",
        "corpus": {
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest": str(config.queries_manifest),
        },
        "evaluated_splits": list(config.evaluated_splits),
        "candidate_universe": candidate_universe,
        "excluded_splits": [config.final_test_split],
        "final_test_status": "not_run",
        "methods": methods,
        "boundary": {
            "text_only": True,
            "network_required": False,
            "gpu_required": False,
            "model_download_required": False,
            "embedding_cache_required": False,
            "external_embeddings_used": False,
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
    retriever: (
        BM25Retriever
        | LexicalCosineRetriever
        | NeuralTextRetriever
        | BM25LexicalRrfRetriever
        | BM25NeuralRrfRetriever
    ),
    queries: Sequence[Any],
    positives: dict[str, tuple[str, ...]],
    *,
    external_embeddings_enabled: bool = False,
    provider_status: dict[str, object] | None = None,
    fusion: dict[str, object] | None = None,
) -> dict[str, object]:
    rankings = {
        query.query_id: tuple(item.page_id for item in retriever.rank(query.query))
        for query in queries
    }
    metrics = compute_retrieval_metrics(rankings=rankings, positives=positives)
    report: dict[str, object] = {
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
    if provider_status is not None:
        report["provider_status"] = provider_status
    if fusion is not None:
        report["fusion"] = fusion
    return report


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
    provider = _provider_name(value.get("provider", "local_stub"))
    return MethodConfig(
        enabled=bool(value.get("enabled", False)),
        external_embeddings_enabled=bool(external.get("enabled", False)),
        provider=provider,
        rrf_k=int(value.get("rrf_k", 60)),
    )


def _candidate_pages(corpus: TextCorpus, config: ReportConfig) -> tuple[TextPage, ...]:
    evaluated_splits = set(config.evaluated_splits)
    if config.candidate_universe == "evaluated_split_pages":
        pages = tuple(page for page in corpus.pages if page.split in evaluated_splits)
    elif config.candidate_universe == "non_train_pages":
        pages = tuple(page for page in corpus.pages if page.split != "train")
    elif config.candidate_universe == "all_pages":
        pages = corpus.pages
    else:
        raise ValueError(f"unknown candidate_universe: {config.candidate_universe}")
    return tuple(sorted(pages, key=lambda page: page.page_id))


def _candidate_universe_report(
    config: ReportConfig,
    pages: Sequence[TextPage],
    queries: Sequence[Any],
) -> dict[str, object]:
    split_counts: dict[str, int] = {}
    for page in pages:
        split_counts[page.split] = split_counts.get(page.split, 0) + 1
    return {
        "name": config.candidate_universe,
        "candidate_page_count": len(pages),
        "candidate_split_counts": dict(sorted(split_counts.items())),
        "evaluated_query_count": len(queries),
        "evaluated_splits": list(config.evaluated_splits),
    }


def _embedding_provider(config: MethodConfig) -> LocalStubEmbeddingProvider:
    if config.external_embeddings_enabled:
        raise ValueError("external neural embeddings are outside Phase 2.5")
    if config.provider != "local_stub":
        raise ValueError("only local_stub neural provider is supported in Phase 2.5")
    return LocalStubEmbeddingProvider()


def _provider_name(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        provider_type = value.get("type", "local_stub")
        if isinstance(provider_type, str):
            return provider_type
    raise ValueError("provider must be a string or object with a string type")


def _required_str(data: dict[str, object], field: str) -> str:
    value = data[field]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
