"""End-to-end diagnostic MVP retrieval pipeline."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from visdoc_retrieve.data_schema import VALID_QUERY_TYPES, ValidationError
from visdoc_retrieve.retrieval_metrics import compute_retrieval_metrics
from visdoc_retrieve.text_retrieval import (
    BM25LexicalRrfRetriever,
    BM25Retriever,
    LexicalCosineRetriever,
    TextCorpus,
    TextPage,
    TextQuery,
    load_text_corpus,
)
from visdoc_retrieve.text_retrieval import (
    RankingItem as TextRankingItem,
)
from visdoc_retrieve.visual_retrieval import (
    MockVisualRetriever,
    VisualCorpus,
    VisualPage,
    VisualQuery,
    build_mock_embedding_cache,
    load_mock_embedding_cache,
    load_visual_corpus,
    write_mock_embedding_cache,
)
from visdoc_retrieve.visual_retrieval import (
    RankingItem as VisualRankingItem,
)


class TextRetriever(Protocol):
    """Minimal text retriever shape used by the MVP pipeline."""

    @property
    def index_size_pages(self) -> int:
        """Return indexed page support."""

    def rank(self, query: str) -> tuple[TextRankingItem, ...]:
        """Rank candidate pages for a query string."""


RankingByQuery = dict[str, tuple[TextRankingItem | VisualRankingItem, ...]]
MVP_COMMAND = (
    "PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json"
)
VISUAL_BOUNDARY_SENTENCE = (
    "The visual late-interaction path is a deterministic mock scaffold and is "
    "not real ColPali or ColQwen execution."
)
MOCK_VISUAL_BRIEF = (
    "deterministic mock scaffold with MaxSim; "
    "not real ColPali or ColQwen execution."
)


@dataclass(frozen=True, slots=True)
class MVPOutputs:
    """Output paths for one MVP run."""

    metrics: Path
    rankings: Path
    run_card: Path
    mock_visual_cache: Path
    human_brief: Path


@dataclass(frozen=True, slots=True)
class MVPConfig:
    """Config for the one-command diagnostic MVP pipeline."""

    name: str
    pages_manifest: Path
    queries_manifest: Path
    evaluated_splits: tuple[str, ...]
    candidate_universe: str
    final_test_split: str
    text_methods: tuple[str, ...]
    visual_methods: tuple[str, ...]
    outputs: MVPOutputs


def load_mvp_config(path: Path) -> MVPConfig:
    """Load a JSON MVP pipeline config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("MVP config must be a JSON object")
    outputs = cast(dict[str, object], data["outputs"])
    return MVPConfig(
        name=_required_str(data, "name"),
        pages_manifest=Path(_required_str(data, "pages_manifest")),
        queries_manifest=Path(_required_str(data, "queries_manifest")),
        evaluated_splits=tuple(cast(list[str], data["evaluated_splits"])),
        candidate_universe=str(
            data.get("candidate_universe", "evaluated_split_pages")
        ),
        final_test_split=_required_str(data, "final_test_split"),
        text_methods=_enabled_methods(data.get("text_methods"), "text"),
        visual_methods=_enabled_methods(data.get("visual_methods"), "visual"),
        outputs=MVPOutputs(
            metrics=Path(_required_str(outputs, "metrics")),
            rankings=Path(_required_str(outputs, "rankings")),
            run_card=Path(_required_str(outputs, "run_card")),
            mock_visual_cache=Path(_required_str(outputs, "mock_visual_cache")),
            human_brief=Path(_required_str(outputs, "human_brief")),
        ),
    )


def run_mvp_pipeline(
    config: MVPConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Run the diagnostic MVP pipeline and persist evidence artifacts."""

    if config.final_test_split in set(config.evaluated_splits):
        raise ValueError("final_test_split must not be included in evaluated_splits")

    text_corpus = load_text_corpus(
        repo_root=repo_root,
        pages_manifest=config.pages_manifest,
        queries_manifest=config.queries_manifest,
    )
    visual_corpus = load_visual_corpus(
        repo_root=repo_root,
        pages_manifest=config.pages_manifest,
        queries_manifest=config.queries_manifest,
    )
    text_queries = tuple(
        sorted(
            (
                query
                for query in text_corpus.queries
                if query.split in set(config.evaluated_splits)
            ),
            key=lambda item: item.query_id,
        )
    )
    visual_queries = tuple(
        visual_corpus.queries_by_id[query.query_id] for query in text_queries
    )
    text_pages = _candidate_text_pages(text_corpus, config)
    visual_pages = _candidate_visual_pages(visual_corpus, config)
    candidate_universe = _candidate_universe_report(config, text_pages, text_queries)
    positives = {
        query.query_id: query.positive_page_ids
        for query in sorted(text_queries, key=lambda item: item.query_id)
    }

    rankings_by_method: dict[str, RankingByQuery] = {}
    method_reports: dict[str, object] = {}
    text_retrievers = _text_retrievers(config.text_methods, text_pages)
    for method_id, retriever in text_retrievers.items():
        rankings = _rank_text_queries(retriever, text_queries)
        rankings_by_method[method_id] = rankings
        method_reports[method_id] = _method_metrics(
            method_id=method_id,
            rankings=rankings,
            queries=text_queries,
            positives=positives,
            candidate_universe=candidate_universe,
            method_kind="text",
            diagnostics={
                "index_size_pages": retriever.index_size_pages,
                "external_embeddings_enabled": False,
            },
        )

    if "mock_visual" in config.visual_methods:
        visual_retriever = MockVisualRetriever(visual_pages)
        visual_rankings = _rank_visual_queries(visual_retriever, visual_queries)
        rankings_by_method["mock_visual"] = visual_rankings
        cache = build_mock_embedding_cache(visual_retriever, visual_queries)
        cache_path = repo_root / config.outputs.mock_visual_cache
        write_mock_embedding_cache(cache_path, cache)
        if load_mock_embedding_cache(cache_path) != cache:
            raise ValidationError("mock visual embedding cache failed round-trip")
        method_reports["mock_visual"] = _method_metrics(
            method_id="mock_visual",
            rankings=visual_rankings,
            queries=text_queries,
            positives=positives,
            candidate_universe=candidate_universe,
            method_kind="visual_mock",
            diagnostics={
                "index_size_pages": visual_retriever.index_size_pages,
                "retriever_id": visual_retriever.retriever_id,
                "provider": "deterministic_mock",
                "cache_path": str(config.outputs.mock_visual_cache),
                "external_model_enabled": visual_retriever.uses_external_model,
                "gpu_required": visual_retriever.gpu_required,
            },
        )

    metrics_report: dict[str, object] = {
        "name": config.name,
        "status": "diagnostic_smoke_only",
        "corpus": {
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest": str(config.queries_manifest),
        },
        "evaluated_splits": list(config.evaluated_splits),
        "candidate_universe": candidate_universe,
        "excluded_splits": [config.final_test_split],
        "final_test_status": "not_run",
        "methods": method_reports,
        "boundary": {
            "diagnostic_smoke_only": True,
            "network_required": False,
            "gpu_required": False,
            "model_download_required": False,
            "external_embeddings_used": False,
            "real_colpali_or_colqwen_execution": False,
            "hard_negative_mining": False,
            "training_run": False,
            "final_test_evaluated": False,
            "benchmark_claim": "none",
        },
        "outputs": {
            "metrics": str(config.outputs.metrics),
            "rankings": str(config.outputs.rankings),
            "run_card": str(config.outputs.run_card),
            "mock_visual_cache": str(config.outputs.mock_visual_cache),
            "human_brief": str(config.outputs.human_brief),
        },
    }

    _write_metrics(repo_root / config.outputs.metrics, metrics_report)
    _write_rankings_csv(
        repo_root / config.outputs.rankings,
        rankings_by_method=rankings_by_method,
        queries=text_queries,
        candidate_universe=config.candidate_universe,
    )
    _write_run_card(repo_root / config.outputs.run_card, metrics_report)
    _write_human_brief(repo_root / config.outputs.human_brief, metrics_report)
    return {
        "metrics": metrics_report,
        "rankings_path": str(config.outputs.rankings),
        "run_card_path": str(config.outputs.run_card),
        "human_brief_path": str(config.outputs.human_brief),
    }


def _enabled_methods(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}_methods must be an object")
    enabled = [
        method_id
        for method_id, method_config in cast(dict[str, object], value).items()
        if isinstance(method_config, dict) and bool(method_config.get("enabled", False))
    ]
    return tuple(enabled)


def _candidate_text_pages(
    corpus: TextCorpus,
    config: MVPConfig,
) -> tuple[TextPage, ...]:
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


def _candidate_visual_pages(
    corpus: VisualCorpus,
    config: MVPConfig,
) -> tuple[VisualPage, ...]:
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
    config: MVPConfig,
    pages: Sequence[TextPage],
    queries: Sequence[TextQuery],
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


def _text_retrievers(
    enabled_methods: Sequence[str],
    pages: Sequence[TextPage],
) -> dict[str, TextRetriever]:
    retrievers: dict[str, TextRetriever] = {}
    for method_id in enabled_methods:
        if method_id == "bm25":
            retrievers[method_id] = BM25Retriever(pages)
        elif method_id == "lexical_cosine":
            retrievers[method_id] = LexicalCosineRetriever(pages)
        elif method_id == "bm25_lexical_rrf":
            retrievers[method_id] = BM25LexicalRrfRetriever(pages)
        elif method_id == "neural_text":
            raise ValueError("neural_text is not enabled in the default MVP")
        else:
            raise ValueError(f"unknown MVP text method: {method_id}")
    return retrievers


def _rank_text_queries(
    retriever: TextRetriever,
    queries: Sequence[TextQuery],
) -> RankingByQuery:
    return {
        query.query_id: retriever.rank(query.query)
        for query in sorted(queries, key=lambda item: item.query_id)
    }


def _rank_visual_queries(
    retriever: MockVisualRetriever,
    queries: Sequence[VisualQuery],
) -> RankingByQuery:
    return {
        query.query_id: retriever.rank(query)
        for query in sorted(queries, key=lambda item: item.query_id)
    }


def _method_metrics(
    *,
    method_id: str,
    rankings: RankingByQuery,
    queries: Sequence[TextQuery],
    positives: Mapping[str, Sequence[str]],
    candidate_universe: Mapping[str, object],
    method_kind: str,
    diagnostics: Mapping[str, object],
) -> dict[str, object]:
    ranking_ids = {
        query_id: tuple(item.page_id for item in ranking)
        for query_id, ranking in rankings.items()
    }
    overall_metrics = compute_retrieval_metrics(
        rankings=ranking_ids,
        positives=positives,
    )
    by_query_type = {
        query_type: _subset_metrics(query_type, ranking_ids, queries, positives)
        for query_type in sorted(VALID_QUERY_TYPES)
    }
    return {
        "method_id": method_id,
        "method_kind": method_kind,
        "status": "diagnostic_smoke_only",
        "overall": {
            "support": len(queries),
            "metrics": overall_metrics.to_dict(),
        },
        "by_query_type": by_query_type,
        "diagnostics": {
            "candidate_universe": dict(candidate_universe),
            "ranked_page_support": _ranked_page_support(ranking_ids),
            **dict(diagnostics),
        },
        "boundary": {
            "diagnostic_only": True,
            "network_required": False,
            "gpu_required": False,
            "model_download_required": False,
            "external_embeddings_used": False,
            "real_colpali_or_colqwen_execution": False,
            "hard_negative_mining": False,
            "training_run": False,
            "final_test_evaluated": False,
            "benchmark_claim": "none",
        },
    }


def _subset_metrics(
    query_type: str,
    rankings: Mapping[str, Sequence[str]],
    queries: Sequence[TextQuery],
    positives: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    subset_query_ids = tuple(
        query.query_id for query in queries if query.query_type == query_type
    )
    if not subset_query_ids:
        return {"support": 0, "metrics": None}
    subset_rankings = {
        query_id: tuple(rankings[query_id]) for query_id in subset_query_ids
    }
    subset_positives = {
        query_id: tuple(positives[query_id]) for query_id in subset_query_ids
    }
    return {
        "support": len(subset_query_ids),
        "metrics": compute_retrieval_metrics(
            rankings=subset_rankings,
            positives=subset_positives,
        ).to_dict(),
    }


def _ranked_page_support(rankings: Mapping[str, Sequence[str]]) -> dict[str, int]:
    if not rankings:
        return {"queries": 0, "min_pages": 0, "max_pages": 0}
    counts = [len(ranking) for ranking in rankings.values()]
    return {
        "queries": len(rankings),
        "min_pages": min(counts),
        "max_pages": max(counts),
    }


def _write_metrics(path: Path, metrics_report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metrics_report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _write_rankings_csv(
    path: Path,
    *,
    rankings_by_method: Mapping[str, RankingByQuery],
    queries: Sequence[TextQuery],
    candidate_universe: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    queries_by_id = {query.query_id: query for query in queries}
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "query_id",
                "query_type",
                "positive_page_ids",
                "candidate_universe",
                "rank",
                "page_id",
                "score",
            ],
        )
        writer.writeheader()
        for method_id in sorted(rankings_by_method):
            for query_id in sorted(rankings_by_method[method_id]):
                query = queries_by_id[query_id]
                for rank_index, item in enumerate(
                    rankings_by_method[method_id][query_id],
                    start=1,
                ):
                    writer.writerow(
                        {
                            "method": method_id,
                            "query_id": query_id,
                            "query_type": query.query_type,
                            "positive_page_ids": ";".join(query.positive_page_ids),
                            "candidate_universe": candidate_universe,
                            "rank": rank_index,
                            "page_id": item.page_id,
                            "score": f"{item.score:.12g}",
                        }
                    )


def _write_run_card(path: Path, metrics_report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = cast(Mapping[str, object], metrics_report["outputs"])
    candidate = cast(Mapping[str, object], metrics_report["candidate_universe"])
    text = f"""# VisDoc MVP Diagnostic Run Card

Status: diagnostic smoke only.

Command:

```bash
{MVP_COMMAND}
```

Inputs:
- Pages manifest: data/synthetic-smoke/pages.jsonl
- Queries/qrels manifest: data/synthetic-smoke/queries.jsonl
- Evaluated split: dev
- Candidate universe: {candidate["name"]}
- Candidate pages: {candidate["candidate_page_count"]}
- Evaluated queries: {candidate["evaluated_query_count"]}

Methods:
- bm25: deterministic text baseline.
- lexical_cosine: deterministic local lexical cosine baseline.
- bm25_lexical_rrf: deterministic reciprocal-rank fusion of BM25 and lexical cosine.
- mock_visual: deterministic mock scaffold using MaxSim over query/page token
  embeddings.

Visual boundary:
{VISUAL_BOUNDARY_SENTENCE}

Claims:
Metrics are diagnostic smoke evidence only. They are not final benchmark results,
retrieval improvement claims, model superiority claims, frozen-test claims, or
production readiness claims.

Not started:
- real ColPali / ColQwen execution
- external embeddings
- hard-negative mining
- LoRA / QLoRA training
- final test evaluation

Evidence:
- Metrics: {outputs["metrics"]}
- Rankings: {outputs["rankings"]}
- Mock visual cache: {outputs["mock_visual_cache"]}
- Human brief: {outputs["human_brief"]}
"""
    path.write_text(text, encoding="utf-8")


def _write_human_brief(path: Path, metrics_report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = cast(Mapping[str, object], metrics_report["candidate_universe"])
    outputs = cast(Mapping[str, object], metrics_report["outputs"])
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>VisDoc MVP Diagnostic Brief</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 32px;
      line-height: 1.55;
      color: #1f2933;
    }}
    main {{ max-width: 920px; margin: 0 auto; }}
    h1 {{ font-size: 28px; margin-bottom: 8px; }}
    h2 {{ font-size: 18px; margin-top: 24px; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
    ul {{ padding-left: 22px; }}
  </style>
</head>
<body>
<main>
  <h1>VisDoc-Retrieve MVP diagnostic smoke brief</h1>
  <p><strong>结论：</strong>本阶段增加了一键运行的最小端到端检索 MVP，
  用固定 synthetic smoke corpus 对比 text baselines 与 deterministic mock
  visual late-interaction scaffold。</p>

  <h2>Current status / 当前状态</h2>
  <p>applying; evidence is diagnostic smoke only and not final benchmark evidence.</p>

  <h2>Inputs and candidate universe / 输入与候选集合</h2>
  <ul>
    <li>Pages: <code>data/synthetic-smoke/pages.jsonl</code></li>
    <li>Queries/qrels: <code>data/synthetic-smoke/queries.jsonl</code></li>
    <li>Evaluated split: <code>dev</code></li>
    <li>Candidate universe: <code>{candidate["name"]}</code></li>
    <li>Candidate pages: {candidate["candidate_page_count"]}; evaluated
    queries: {candidate["evaluated_query_count"]}</li>
  </ul>

  <h2>Baselines / 方法</h2>
  <ul>
    <li><code>bm25</code>: deterministic text baseline.</li>
    <li><code>lexical_cosine</code>: deterministic local lexical cosine
    baseline, not external dense embedding.</li>
    <li><code>bm25_lexical_rrf</code>: deterministic BM25 + lexical cosine RRF.</li>
    <li><code>mock_visual</code>: {MOCK_VISUAL_BRIEF}</li>
  </ul>

  <h2>Evidence / 证据路径</h2>
  <ul>
    <li><code>{outputs["metrics"]}</code></li>
    <li><code>{outputs["rankings"]}</code></li>
    <li><code>{outputs["run_card"]}</code></li>
    <li><code>{outputs["mock_visual_cache"]}</code></li>
  </ul>

  <h2>Limits / 不夸大的边界</h2>
  <p>Metrics are diagnostic smoke only. Real ColPali / ColQwen execution,
  external embeddings, hard-negative mining, LoRA / QLoRA training, and final
  test evaluation have not started.</p>

  <h2>Reproduce / 复现</h2>
  <p><code>{MVP_COMMAND}</code></p>
</main>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _required_str(data: Mapping[str, object], field: str) -> str:
    value = data[field]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value
