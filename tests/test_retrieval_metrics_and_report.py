"""Tests for retrieval metrics and diagnostic text-baseline reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from visdoc_retrieve.retrieval_metrics import compute_retrieval_metrics
from visdoc_retrieve.text_baseline_report import (
    MethodConfig,
    ReportConfig,
    load_report_config,
    run_text_baseline_report,
)


def test_retrieval_metrics_match_known_positive_positions() -> None:
    metrics = compute_retrieval_metrics(
        rankings={
            "q1": ("p1", "p2", "p3"),
            "q2": ("p3", "p2", "p1"),
            "q3": ("p4", "p5", "p6"),
        },
        positives={
            "q1": ("p1",),
            "q2": ("p1",),
            "q3": ("p9",),
        },
    )

    assert metrics.evaluated_queries == 3
    assert metrics.ranked_pages_per_query == 3
    assert metrics.recall_at_1 == 1 / 3
    assert metrics.recall_at_5 == 2 / 3
    assert metrics.mrr == (1 + 1 / 3) / 3
    assert round(metrics.ndcg_at_10, 6) == round((1 + 0.5) / 3, 6)


def test_recall_metrics_count_fraction_of_multiple_positive_pages() -> None:
    metrics = compute_retrieval_metrics(
        rankings={"q1": ("p1", "x", "p2", "p3")},
        positives={"q1": ("p1", "p2", "p9")},
    )

    assert metrics.recall_at_1 == 1 / 3
    assert metrics.recall_at_5 == 2 / 3
    assert metrics.mrr == 1
    assert round(metrics.ndcg_at_10, 6) == round(1.5 / 2.1309297535714578, 6)


def test_report_runner_generates_diagnostic_methods_and_excludes_final_test(
    tmp_path: Path,
) -> None:
    config = load_report_config(Path("configs/text-baselines-synthetic-smoke.json"))
    output_path = tmp_path / "text-baselines-report.json"

    report = run_text_baseline_report(
        config,
        repo_root=Path.cwd(),
        output_path=output_path,
    )
    persisted = json.loads(output_path.read_text(encoding="utf-8"))

    assert persisted == report
    assert report["status"] == "diagnostic_only"
    assert report["final_test_status"] == "not_run"
    assert report["evaluated_splits"] == ["dev"]
    assert sorted(report["methods"]) == ["bm25", "dense_text", "hybrid_rrf"]

    for method in report["methods"].values():
        assert method["diagnostics"]["latency_per_query_ms"]["label"] == "diagnostic"
        assert method["diagnostics"]["index_size_pages"]["value"] == 8
        assert method["hard_negative_hit_rate"] == {
            "status": "not_available",
            "support": 0,
        }
        assert method["metrics"]["evaluated_queries"] == 24

    report_text = json.dumps(report, sort_keys=True).lower()
    forbidden = ("colpali", "colqwen", "adapter improvement", "final benchmark")
    assert not any(term in report_text for term in forbidden)


def test_report_runner_rejects_config_that_evaluates_final_test_split(
    tmp_path: Path,
) -> None:
    bad_config = ReportConfig(
        name="bad-final-test-config",
        pages_manifest=Path("data/synthetic-smoke/pages.jsonl"),
        queries_manifest=Path("data/synthetic-smoke/queries.jsonl"),
        evaluated_splits=("dev", "test"),
        final_test_split="test",
        output_path=tmp_path / "should-not-write.json",
        methods={"bm25": MethodConfig(enabled=True)},
    )

    with pytest.raises(ValueError, match="final_test_split"):
        run_text_baseline_report(
            bad_config,
            repo_root=Path.cwd(),
            output_path=tmp_path / "should-not-write.json",
        )

    assert not (tmp_path / "should-not-write.json").exists()
