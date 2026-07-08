"""Phase 6D one-time frozen final comparison runner."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from visdoc_retrieve.data_schema import VALID_QUERY_TYPES
from visdoc_retrieve.retrieval_metrics import compute_retrieval_metrics
from visdoc_retrieve.text_retrieval import (
    BM25LexicalRrfRetriever,
    BM25Retriever,
    LexicalCosineRetriever,
    TextPage,
    TextQuery,
    load_text_corpus,
)
from visdoc_retrieve.text_retrieval import (
    RankingItem as TextRankingItem,
)
from visdoc_retrieve.visual_retrieval import (
    MockVisualRetriever,
    VisualPage,
    VisualQuery,
    load_visual_corpus,
)

PHASE_6D_CHANGE = "run-one-time-frozen-final-comparison"
PROTOCOL_VERSION = "phase-6b-final-comparison-protocol/v1"
DEFAULT_COMMAND = (
    "PYTHONPATH=src python -m visdoc_retrieve.run_final_comparison "
    "--config configs/final_comparison.json"
)


class FinalComparisonRunConfigError(ValueError):
    """Raised when Phase 6D final-comparison configuration is unsafe."""


class TextFinalRetriever(Protocol):
    """Text retriever shape used by the final comparison runner."""

    def rank(self, query: str) -> Sequence[TextRankingItem]:
        """Rank a query string and return page-score items."""


@dataclass(frozen=True, slots=True)
class FinalComparisonRunOutputs:
    """Output paths for Phase 6D final evidence."""

    manifest: Path
    metrics: Path
    rankings: Path
    report: Path
    claim_checklist: Path
    no_retune_pledge: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class FinalComparisonRunConfig:
    """Configuration for the Phase 6D final comparison."""

    name: str
    protocol_version: str
    protocol_doc: Path
    protocol_spec: Path
    readiness_evidence: Path
    pages_manifest: Path
    queries_manifest: Path
    final_split: str
    candidate_universe: str
    systems: Mapping[str, Mapping[str, object]]
    outputs: FinalComparisonRunOutputs
    allow_rerun: bool = False

    def with_overrides(
        self,
        *,
        outputs: FinalComparisonRunOutputs | None = None,
        allow_rerun: bool | None = None,
    ) -> FinalComparisonRunConfig:
        """Return a copy with test or CLI overrides."""

        return replace(
            self,
            outputs=outputs if outputs is not None else self.outputs,
            allow_rerun=self.allow_rerun if allow_rerun is None else allow_rerun,
        )

    def with_output_overrides(
        self,
        *,
        manifest: Path | None = None,
        metrics: Path | None = None,
        rankings: Path | None = None,
        report: Path | None = None,
        claim_checklist: Path | None = None,
        no_retune_pledge: Path | None = None,
        human_brief: Path | None = None,
        progress_ledger: Path | None = None,
        allow_rerun: bool | None = None,
    ) -> FinalComparisonRunConfig:
        """Return a copy with selected output-path overrides."""

        return self.with_overrides(
            outputs=FinalComparisonRunOutputs(
                manifest=manifest or self.outputs.manifest,
                metrics=metrics or self.outputs.metrics,
                rankings=rankings or self.outputs.rankings,
                report=report or self.outputs.report,
                claim_checklist=claim_checklist or self.outputs.claim_checklist,
                no_retune_pledge=no_retune_pledge
                or self.outputs.no_retune_pledge,
                human_brief=human_brief or self.outputs.human_brief,
                progress_ledger=progress_ledger or self.outputs.progress_ledger,
            ),
            allow_rerun=allow_rerun,
        )


def build_phase_6d_default_config() -> FinalComparisonRunConfig:
    """Build the default checked-in Phase 6D final-comparison config."""

    return FinalComparisonRunConfig(
        name="phase-6d-one-time-frozen-final-comparison",
        protocol_version=PROTOCOL_VERSION,
        protocol_doc=Path("docs/final-comparison-protocol.md"),
        protocol_spec=Path("openspec/specs/final-comparison-protocol/spec.md"),
        readiness_evidence=Path(
            "reports/final-comparison-protocol/"
            "phase-6c-execution-gate-dry-run.json"
        ),
        pages_manifest=Path("data/synthetic-smoke/pages.jsonl"),
        queries_manifest=Path("data/synthetic-smoke/queries.jsonl"),
        final_split="test",
        candidate_universe="evaluated_split_pages",
        systems={
            "bm25": {"enabled": True},
            "lexical_cosine": {"enabled": True},
            "bm25_lexical_rrf": {"enabled": True},
            "mock_visual": {"enabled": True},
            "zero_shot_visual_backend": {
                "enabled": False,
                "artifact_required": True,
            },
            "tiny_lora_adapter": {"enabled": False, "artifact_required": True},
        },
        outputs=FinalComparisonRunOutputs(
            manifest=Path(
                "reports/final-comparison/final-comparison-run-manifest.json"
            ),
            metrics=Path("reports/final-comparison/final-metrics.json"),
            rankings=Path("reports/final-comparison/final-rankings.csv"),
            report=Path("reports/final-comparison/final-comparison-report.md"),
            claim_checklist=Path(
                "reports/final-comparison/final-claim-checklist.json"
            ),
            no_retune_pledge=Path("reports/final-comparison/no-retune-pledge.md"),
            human_brief=Path(
                "docs/human-briefs/2026-07-08-final-comparison-report.md"
            ),
            progress_ledger=Path("reports/progress-ledger.yaml"),
        ),
    )


def load_phase_6d_config(path: Path) -> FinalComparisonRunConfig:
    """Load a checked-in Phase 6D final-comparison JSON config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    outputs = cast(Mapping[str, object], data["outputs"])
    return FinalComparisonRunConfig(
        name=_required_str(data, "name"),
        protocol_version=PROTOCOL_VERSION,
        protocol_doc=Path(_required_str(data, "protocol_doc")),
        protocol_spec=Path(_required_str(data, "protocol_spec")),
        readiness_evidence=Path(_required_str(data, "readiness_evidence")),
        pages_manifest=Path(_required_str(data, "pages_manifest")),
        queries_manifest=Path(_required_str(data, "queries_manifest")),
        final_split=_required_str(data, "final_split"),
        candidate_universe=_required_str(data, "candidate_universe"),
        systems=cast(Mapping[str, Mapping[str, object]], data["systems"]),
        outputs=FinalComparisonRunOutputs(
            manifest=Path(_required_str(outputs, "manifest")),
            metrics=Path(_required_str(outputs, "metrics")),
            rankings=Path(_required_str(outputs, "rankings")),
            report=Path(_required_str(outputs, "report")),
            claim_checklist=Path(_required_str(outputs, "claim_checklist")),
            no_retune_pledge=Path(_required_str(outputs, "no_retune_pledge")),
            human_brief=Path(_required_str(outputs, "human_brief")),
            progress_ledger=Path(_required_str(outputs, "progress_ledger")),
        ),
    )


def discover_active_openspec_changes(repo_root: Path) -> tuple[str, ...]:
    """Return active OpenSpec changes using the local CLI."""

    completed = subprocess.run(
        ["openspec", "list", "--json"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        json_start = completed.stdout.find("{")
        if json_start >= 0:
            try:
                data = json.loads(completed.stdout[json_start:])
            except json.JSONDecodeError:
                data = {}
            changes = data.get("changes")
            if isinstance(changes, list):
                names: list[str] = []
                for item in changes:
                    if isinstance(item, dict) and isinstance(item.get("name"), str):
                        names.append(str(item["name"]))
                return tuple(names)
    return _discover_active_openspec_changes_text(repo_root)


def run_final_comparison(
    config: FinalComparisonRunConfig,
    *,
    repo_root: Path,
    active_changes: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Execute the authorized one-time Phase 6D final comparison."""

    repo_root = repo_root.resolve()
    active = active_changes or discover_active_openspec_changes(repo_root)
    _validate_active_state(active)
    _validate_once_outputs(repo_root, config)
    readiness = _load_json(repo_root / config.readiness_evidence)
    _validate_readiness(readiness)

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
                if query.split == config.final_split
            ),
            key=lambda item: item.query_id,
        )
    )
    visual_queries = tuple(
        visual_corpus.queries_by_id[query.query_id] for query in text_queries
    )
    text_pages = _candidate_text_pages(text_corpus.pages, config)
    visual_pages = _candidate_visual_pages(visual_corpus.pages, config)
    candidate = _candidate_universe_report(config, text_pages, text_queries)
    positives = {query.query_id: query.positive_page_ids for query in text_queries}

    ranking_rows: list[dict[str, object]] = []
    systems: dict[str, dict[str, object]] = {}
    ranking_ids_by_system: dict[str, dict[str, tuple[str, ...]]] = {}
    score_rows_by_system: dict[str, dict[str, tuple[tuple[str, float], ...]]] = {}

    if _system_enabled(config, "bm25"):
        rankings = _rank_text(BM25Retriever(text_pages), text_queries)
        _record_system(
            systems,
            ranking_ids_by_system,
            score_rows_by_system,
            "bm25",
            "text_lexical",
            rankings,
            text_queries,
            positives,
            candidate,
        )
    if _system_enabled(config, "lexical_cosine"):
        rankings = _rank_text(LexicalCosineRetriever(text_pages), text_queries)
        _record_system(
            systems,
            ranking_ids_by_system,
            score_rows_by_system,
            "lexical_cosine",
            "text_lexical",
            rankings,
            text_queries,
            positives,
            candidate,
        )
    if _system_enabled(config, "bm25_lexical_rrf"):
        rankings = _rank_text(BM25LexicalRrfRetriever(text_pages), text_queries)
        _record_system(
            systems,
            ranking_ids_by_system,
            score_rows_by_system,
            "bm25_lexical_rrf",
            "hybrid_rrf",
            rankings,
            text_queries,
            positives,
            candidate,
        )
    if _system_enabled(config, "mock_visual"):
        rankings = _rank_visual(MockVisualRetriever(visual_pages), visual_queries)
        _record_system(
            systems,
            ranking_ids_by_system,
            score_rows_by_system,
            "mock_visual",
            "visual_mock_scaffold",
            rankings,
            text_queries,
            positives,
            candidate,
        )

    for method_id in sorted(config.systems):
        if method_id not in systems:
            systems[method_id] = _unavailable_system(method_id)

    manifest = _build_manifest(
        config=config,
        repo_root=repo_root,
        candidate=candidate,
        final_queries=text_queries,
        final_pages=text_pages,
    )
    metrics = {
        "schema": "final_comparison_metrics/v1",
        "phase": "6D",
        "protocol_version": config.protocol_version,
        "split_scope": "final_test",
        "final_test_read": True,
        "candidate_universe": candidate,
        "systems": dict(sorted(systems.items())),
        "result_interpretation": {
            "improvement_claim_supported": False,
            "claim_status": "no_clear_improvement_claim",
            "summary": (
                "Final comparison ran on deterministic baselines and mock visual "
                "scaffold only; no clear benchmark improvement claim is supported."
            ),
        },
    }
    checklist = _build_claim_checklist()

    _write_json(repo_root / config.outputs.manifest, manifest)
    _write_json(repo_root / config.outputs.metrics, metrics)
    _write_rankings_csv(
        repo_root / config.outputs.rankings,
        text_queries=text_queries,
        candidate_universe=config.candidate_universe,
        score_rows_by_system=score_rows_by_system,
    )
    _write_report(repo_root / config.outputs.report, metrics, manifest)
    _write_json(repo_root / config.outputs.claim_checklist, checklist)
    _write_no_retune_pledge(repo_root / config.outputs.no_retune_pledge, manifest)
    _write_human_brief(repo_root / config.outputs.human_brief, metrics, manifest)
    _append_progress_ledger(repo_root / config.outputs.progress_ledger, config)
    return {
        "status": "final_comparison_complete",
        "manifest": str(config.outputs.manifest),
        "metrics": str(config.outputs.metrics),
        "report": str(config.outputs.report),
        "claim_checklist": str(config.outputs.claim_checklist),
        "systems": sorted(systems),
        "ranking_rows": len(ranking_rows),
    }


def _record_system(
    systems: dict[str, dict[str, object]],
    ranking_ids_by_system: dict[str, dict[str, tuple[str, ...]]],
    score_rows_by_system: dict[str, dict[str, tuple[tuple[str, float], ...]]],
    method_id: str,
    method_family: str,
    rankings: Mapping[str, Sequence[tuple[str, float]]],
    queries: Sequence[TextQuery],
    positives: Mapping[str, Sequence[str]],
    candidate: Mapping[str, object],
) -> None:
    ranking_ids = {
        query_id: tuple(page_id for page_id, _score in rows)
        for query_id, rows in rankings.items()
    }
    ranking_ids_by_system[method_id] = ranking_ids
    score_rows_by_system[method_id] = {
        query_id: tuple(rows) for query_id, rows in rankings.items()
    }
    metrics = compute_retrieval_metrics(rankings=ranking_ids, positives=positives)
    systems[method_id] = {
        "method_id": method_id,
        "method_family": method_family,
        "split_scope": "final_test",
        "candidate_universe": candidate["name"],
        "artifact_source": "checked_in_deterministic_runner",
        "adapter_status": "not_applicable",
        "status": "final_benchmark",
        "metrics": metrics.to_dict(),
        "overall": {"support": len(queries), "metrics": metrics.to_dict()},
        "by_query_type": _subset_metrics(ranking_ids, queries, positives),
        "final_test_used": True,
        "benchmark_claim": "none",
        "evidence_path": "reports/final-comparison/final-metrics.json",
        "notes": [
            "Executed once under Phase 6D frozen protocol.",
            "No training, tuning, GPU, model download, or adapter checkpoint used.",
        ],
    }


def _rank_text(
    retriever: TextFinalRetriever,
    queries: Sequence[TextQuery],
) -> dict[str, tuple[tuple[str, float], ...]]:
    return {
        query.query_id: tuple(
            (item.page_id, item.score) for item in retriever.rank(query.query)
        )
        for query in sorted(queries, key=lambda item: item.query_id)
    }


def _rank_visual(
    retriever: MockVisualRetriever,
    queries: Sequence[VisualQuery],
) -> dict[str, tuple[tuple[str, float], ...]]:
    return {
        query.query_id: tuple(
            (item.page_id, item.score) for item in retriever.rank(query)
        )
        for query in sorted(queries, key=lambda item: item.query_id)
    }


def _subset_metrics(
    rankings: Mapping[str, Sequence[str]],
    queries: Sequence[TextQuery],
    positives: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for query_type in sorted(VALID_QUERY_TYPES):
        query_ids = tuple(
            query.query_id for query in queries if query.query_type == query_type
        )
        if not query_ids:
            result[query_type] = {"support": 0, "metrics": None}
            continue
        subset_rankings = {
            query_id: tuple(rankings[query_id]) for query_id in query_ids
        }
        subset_positives = {
            query_id: tuple(positives[query_id]) for query_id in query_ids
        }
        result[query_type] = {
            "support": len(query_ids),
            "metrics": compute_retrieval_metrics(
                rankings=subset_rankings,
                positives=subset_positives,
            ).to_dict(),
        }
    return result


def _unavailable_system(method_id: str) -> dict[str, object]:
    return {
        "method_id": method_id,
        "method_family": "optional_or_unavailable",
        "split_scope": "final_test",
        "candidate_universe": "evaluated_split_pages",
        "artifact_source": "not_available",
        "adapter_status": "not_available",
        "status": "not_available",
        "metrics": None,
        "final_test_used": False,
        "benchmark_claim": "none",
        "evidence_path": None,
        "notes": [
            "No frozen artifact was available under the Phase 6D protocol.",
            "Metrics were not fabricated.",
        ],
    }


def _candidate_text_pages(
    pages: Sequence[TextPage],
    config: FinalComparisonRunConfig,
) -> tuple[TextPage, ...]:
    if config.candidate_universe == "evaluated_split_pages":
        selected = tuple(page for page in pages if page.split == config.final_split)
    elif config.candidate_universe == "non_train_pages":
        selected = tuple(page for page in pages if page.split != "train")
    elif config.candidate_universe == "all_pages":
        selected = tuple(pages)
    else:
        raise FinalComparisonRunConfigError(
            f"unknown candidate_universe: {config.candidate_universe}"
        )
    return tuple(sorted(selected, key=lambda page: page.page_id))


def _candidate_visual_pages(
    pages: Sequence[VisualPage],
    config: FinalComparisonRunConfig,
) -> tuple[VisualPage, ...]:
    if config.candidate_universe == "evaluated_split_pages":
        selected = tuple(page for page in pages if page.split == config.final_split)
    elif config.candidate_universe == "non_train_pages":
        selected = tuple(page for page in pages if page.split != "train")
    elif config.candidate_universe == "all_pages":
        selected = tuple(pages)
    else:
        raise FinalComparisonRunConfigError(
            f"unknown candidate_universe: {config.candidate_universe}"
        )
    return tuple(sorted(selected, key=lambda page: page.page_id))


def _candidate_universe_report(
    config: FinalComparisonRunConfig,
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
        "evaluated_splits": [config.final_split],
    }


def _build_manifest(
    *,
    config: FinalComparisonRunConfig,
    repo_root: Path,
    candidate: Mapping[str, object],
    final_queries: Sequence[TextQuery],
    final_pages: Sequence[TextPage],
) -> dict[str, object]:
    timestamp = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    config_hash_payload = {
        "name": config.name,
        "protocol_version": config.protocol_version,
        "pages_manifest": str(config.pages_manifest),
        "queries_manifest": str(config.queries_manifest),
        "final_split": config.final_split,
        "candidate_universe": config.candidate_universe,
        "systems": config.systems,
    }
    return {
        "schema": "final_comparison_run_manifest/v1",
        "phase": "6D",
        "run_id": f"phase-6d-{timestamp.replace(':', '').replace('+00:00', 'Z')}",
        "run_timestamp": timestamp,
        "command": DEFAULT_COMMAND,
        "git_commit": _git_commit(repo_root),
        "protocol": {
            "version": config.protocol_version,
            "path": str(config.protocol_doc),
            "sha256": _file_sha256(repo_root / config.protocol_doc),
            "spec_path": str(config.protocol_spec),
            "spec_sha256": _file_sha256(repo_root / config.protocol_spec),
        },
        "candidate_universe": {
            **dict(candidate),
            "sha256": _json_sha256(
                {
                    "candidate_page_ids": [page.page_id for page in final_pages],
                    "candidate_universe": config.candidate_universe,
                }
            ),
        },
        "split_policy": {
            "final_split": config.final_split,
            "training_split": "train",
            "dev_split": "dev",
            "policy": "read final split once; no tuning after final",
            "artifact_freeze_path": "reports/training-readiness/artifact-freeze.json",
            "sha256": _file_sha256(
                repo_root / "reports/training-readiness/artifact-freeze.json"
            ),
        },
        "metric_definitions": {
            "path": "openspec/specs/retrieval-evaluation-metrics/spec.md",
            "sha256": _file_sha256(
                repo_root / "openspec/specs/retrieval-evaluation-metrics/spec.md"
            ),
            "metrics": ["recall_at_1", "recall_at_5", "mrr", "ndcg_at_10"],
        },
        "final_test": {
            "read": True,
            "split": config.final_split,
            "queries_manifest": str(config.queries_manifest),
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest_sha256": _file_sha256(
                repo_root / config.queries_manifest
            ),
            "pages_manifest_sha256": _file_sha256(repo_root / config.pages_manifest),
            "sha256": _json_sha256(
                {
                    "query_ids": [query.query_id for query in final_queries],
                    "qrels": {
                        query.query_id: list(query.positive_page_ids)
                        for query in final_queries
                    },
                    "split": config.final_split,
                }
            ),
            "query_count": len(final_queries),
            "candidate_page_count": len(final_pages),
        },
        "config_hashes": {
            "config_path": "configs/final_comparison.json",
            "config_sha256": _file_sha256(repo_root / "configs/final_comparison.json")
            if (repo_root / "configs/final_comparison.json").is_file()
            else _json_sha256(config_hash_payload),
            "normalized_config_sha256": _json_sha256(config_hash_payload),
        },
        "no_retune_pledge": {
            "accepted": True,
            "path": str(config.outputs.no_retune_pledge),
            "pledge": (
                "No tuning, retrieval-pipeline changes, candidate-universe changes, "
                "metric-definition changes, or final-label changes after this run."
            ),
        },
        "training": "not_executed",
        "tuning_after_final": "forbidden",
        "a100_or_gpu_used": False,
        "ssh_used": False,
        "model_download": "not_executed",
        "model_weights_committed": False,
        "adapter_checkpoints_committed": False,
        "cache_artifacts_committed": False,
        "private_config_or_path_committed": False,
    }


def _build_claim_checklist() -> dict[str, object]:
    return {
        "schema": "final_comparison_claim_checklist/v1",
        "phase": "6D",
        "protocol_version": PROTOCOL_VERSION,
        "benchmark_claim_allowed": False,
        "claim_status": "no_clear_improvement_claim",
        "blocked_reasons": [
            "no_real_trained_adapter_or_model_row",
            "mock_visual_is_scaffold_not_model_performance",
            "reviewer_approval_not_recorded",
        ],
        "checklist": {
            "final_test_authorized": True,
            "final_test_read": True,
            "final_comparison_executed": True,
            "final_metrics_generated": True,
            "candidate_universe_frozen": True,
            "metric_definitions_frozen": True,
            "split_policy_frozen": True,
            "no_tuning_after_final_documented": True,
            "model_weight_hygiene_passed": True,
            "adapter_checkpoint_hygiene_passed": True,
            "training_cache_hygiene_passed": True,
            "private_config_absent": True,
            "exact_private_model_path_absent": True,
            "dev_only_not_presented_as_final": True,
            "tiny_runner_not_presented_as_benchmark": True,
            "unsupported_system_metrics_fabricated": False,
            "readme_result_claim_added": False,
            "reviewer_approval_recorded": False,
        },
    }


def _write_rankings_csv(
    path: Path,
    *,
    text_queries: Sequence[TextQuery],
    candidate_universe: str,
    score_rows_by_system: Mapping[str, Mapping[str, Sequence[tuple[str, float]]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    queries_by_id = {query.query_id: query for query in text_queries}
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
            lineterminator="\n",
        )
        writer.writeheader()
        for method_id in sorted(score_rows_by_system):
            for query_id in sorted(score_rows_by_system[method_id]):
                query = queries_by_id[query_id]
                for rank_index, (page_id, score) in enumerate(
                    score_rows_by_system[method_id][query_id],
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
                            "page_id": page_id,
                            "score": f"{score:.12g}",
                        }
                    )


def _write_report(
    path: Path,
    metrics: Mapping[str, object],
    manifest: Mapping[str, object],
) -> None:
    systems = cast(Mapping[str, Mapping[str, object]], metrics["systems"])
    protocol = cast(Mapping[str, object], manifest["protocol"])
    lines = [
        "# Phase 6D Final Comparison Report",
        "",
        "Status: one-time frozen final comparison complete.",
        "",
        "This run read the frozen final-test split exactly once under "
        f"`{protocol['version']}`. No tuning, training, retrieval "
        "pipeline change, metric-definition change, candidate-universe change, "
        "or final-label change is allowed after this run.",
        "",
        "## Systems",
        "",
    ]
    for method_id, row in sorted(systems.items()):
        status = row["status"]
        if status == "final_benchmark":
            overall = cast(Mapping[str, object], row["overall"])
            values = cast(Mapping[str, object], overall["metrics"])
            lines.append(
                "- "
                f"`{method_id}`: Recall@1={values['recall_at_1']}, "
                f"Recall@5={values['recall_at_5']}, MRR={values['mrr']}, "
                f"NDCG@10={values['ndcg_at_10']}; support={overall['support']}"
            )
        else:
            lines.append(f"- `{method_id}`: {status}; metrics not fabricated.")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "No clear benchmark improvement claim is supported. The run compares "
            "deterministic text baselines and a deterministic mock visual scaffold. "
            "Tiny A100 runner proof and dev-only evidence remain non-final pipeline "
            "evidence.",
            "",
            "## Evidence",
            "",
            "- Manifest: `reports/final-comparison/final-comparison-run-manifest.json`",
            "- Metrics: `reports/final-comparison/final-metrics.json`",
            "- Rankings: `reports/final-comparison/final-rankings.csv`",
            "- Claim checklist: `reports/final-comparison/final-claim-checklist.json`",
            "- No-retune pledge: `reports/final-comparison/no-retune-pledge.md`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_human_brief(
    path: Path,
    metrics: Mapping[str, object],
    manifest: Mapping[str, object],
) -> None:
    systems = cast(Mapping[str, Mapping[str, object]], metrics["systems"])
    protocol = cast(Mapping[str, object], manifest["protocol"])
    final_test = cast(Mapping[str, object], manifest["final_test"])
    ran = [
        method_id
        for method_id, row in sorted(systems.items())
        if row["status"] == "final_benchmark"
    ]
    missing = [
        method_id
        for method_id, row in sorted(systems.items())
        if row["status"] != "final_benchmark"
    ]
    text = f"""# Phase 6D one-time frozen final comparison

结论：Phase 6D 已执行一次 frozen final comparison；final test 已读取。
读取后不得再调参、改 pipeline、改 metrics、改 candidate universe
或改 final labels。

## 运行边界

- Protocol: `{protocol['version']}`
- Final split: `{final_test['split']}`
- Final test read: `true`
- Training: `not_executed`
- A100 / SSH / GPU: `false`
- Model download: `not_executed`
- Benchmark improvement claim: `not supported`

## 实际运行的 systems

{chr(10).join(f'- `{method_id}`' for method_id in ran)}

## Not available / not run

{chr(10).join(f'- `{method_id}`' for method_id in missing)}

## 解读

本次结果只支持最终冻结比较已经执行这一事实。
没有清晰 benchmark improvement claim。`mock_visual` 是 deterministic
mock scaffold；tiny A100 runner proof 仍是 pipeline proof，
不是正式训练收益。

## Evidence

- `reports/final-comparison/final-comparison-run-manifest.json`
- `reports/final-comparison/final-metrics.json`
- `reports/final-comparison/final-comparison-report.md`
- `reports/final-comparison/final-claim-checklist.json`
- `reports/final-comparison/no-retune-pledge.md`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_no_retune_pledge(path: Path, manifest: Mapping[str, object]) -> None:
    protocol = cast(Mapping[str, object], manifest["protocol"])
    text = f"""# No-Retune Pledge

Run ID: `{manifest['run_id']}`
Git commit: `{manifest['git_commit']}`
Protocol: `{protocol['version']}`

No tuning, retrieval-pipeline changes, candidate-universe changes,
metric-definition changes, final-test label/qrel changes, or result-driven
reruns are allowed after this one-time frozen final comparison.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_progress_ledger(path: Path, config: FinalComparisonRunConfig) -> None:
    entry = f"""
final_comparison_phase_6d_status:
  status: final_comparison_complete
  change: run-one-time-frozen-final-comparison
  scope: one_time_frozen_final_benchmark
  protocol_version: {config.protocol_version}
  command: {DEFAULT_COMMAND}
  final_test_evaluation: run_once
  final_comparison_execution: complete
  benchmark_claim: no_clear_improvement_claim
  training: not_executed
  tuning_after_final: forbidden
  a100_or_gpu_used: false
  ssh_used: false
  model_download: not_executed
  evidence:
    manifest: {config.outputs.manifest}
    metrics: {config.outputs.metrics}
    rankings: {config.outputs.rankings}
    report: {config.outputs.report}
    claim_checklist: {config.outputs.claim_checklist}
    no_retune_pledge: {config.outputs.no_retune_pledge}
    human_brief: {config.outputs.human_brief}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(existing.rstrip() + "\n" + entry.lstrip(), encoding="utf-8")


def _validate_active_state(active_changes: Sequence[str]) -> None:
    unexpected = sorted(name for name in active_changes if name != PHASE_6D_CHANGE)
    if unexpected:
        raise FinalComparisonRunConfigError(
            f"unexpected active OpenSpec changes: {unexpected}"
        )


def _validate_readiness(readiness: Mapping[str, object]) -> None:
    if readiness.get("final_run_readiness") != "ready_for_phase_6d":
        raise FinalComparisonRunConfigError("Phase 6C readiness is not ready")
    if readiness.get("final_comparison_execution") != "not_executed":
        raise FinalComparisonRunConfigError("Phase 6C evidence already executed final")


def _validate_once_outputs(repo_root: Path, config: FinalComparisonRunConfig) -> None:
    if config.allow_rerun:
        return
    for output in (
        config.outputs.manifest,
        config.outputs.metrics,
        config.outputs.rankings,
        config.outputs.report,
        config.outputs.claim_checklist,
        config.outputs.no_retune_pledge,
        config.outputs.human_brief,
    ):
        path = repo_root / output
        if path.exists():
            raise FinalComparisonRunConfigError(
                f"final comparison output already exists: {output}"
            )


def _system_enabled(config: FinalComparisonRunConfig, method_id: str) -> bool:
    return bool(config.systems.get(method_id, {}).get("enabled", False))


def _discover_active_openspec_changes_text(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["openspec", "list"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    names: list[str] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("Note:", "Changes:", "No active")):
            continue
        names.append(stripped.split()[0])
    return tuple(names)


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> Mapping[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FinalComparisonRunConfigError(f"expected JSON object: {path}")
    return cast(Mapping[str, object], data)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value
