"""Tests for retrieval metrics and diagnostic text-baseline reports."""

from __future__ import annotations

import json
from dataclasses import replace
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

    assert config.candidate_universe == "evaluated_split_pages"

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
    assert report["candidate_universe"] == {
        "name": "evaluated_split_pages",
        "candidate_page_count": 8,
        "candidate_split_counts": {"dev": 8},
        "evaluated_query_count": 24,
        "evaluated_splits": ["dev"],
    }
    assert sorted(report["methods"]) == [
        "bm25",
        "bm25_lexical_rrf",
        "bm25_neural_rrf",
        "lexical_cosine",
        "neural_text",
    ]

    for method in report["methods"].values():
        assert method["diagnostics"]["latency_per_query_ms"]["label"] == "diagnostic"
        assert method["diagnostics"]["index_size_pages"]["value"] == 8
        assert method["diagnostics"]["ranked_page_support"] == {
            "queries": 24,
            "min_pages": 8,
            "max_pages": 8,
        }
        assert method["hard_negative_hit_rate"] == {
            "status": "not_available",
            "support": 0,
        }
        assert method["metrics"]["evaluated_queries"] == 24
        assert method["metrics"]["ranked_pages_per_query"] == 8

    report_text = json.dumps(report, sort_keys=True).lower()
    forbidden = (
        "colpali",
        "colqwen",
        "adapter improvement",
        "final benchmark",
        "dense_text",
    )
    assert not any(term in report_text for term in forbidden)


def test_report_candidate_universe_can_widen_candidates_without_final_test_queries(
    tmp_path: Path,
) -> None:
    base_config = load_report_config(
        Path("configs/text-baselines-synthetic-smoke.json")
    )

    non_train_report = run_text_baseline_report(
        replace(
            base_config,
            candidate_universe="non_train_pages",
            methods={"bm25": MethodConfig(enabled=True)},
        ),
        repo_root=Path.cwd(),
        output_path=tmp_path / "non-train-pages.json",
    )
    all_pages_report = run_text_baseline_report(
        replace(
            base_config,
            candidate_universe="all_pages",
            methods={"bm25": MethodConfig(enabled=True)},
        ),
        repo_root=Path.cwd(),
        output_path=tmp_path / "all-pages.json",
    )

    assert non_train_report["final_test_status"] == "not_run"
    assert non_train_report["candidate_universe"] == {
        "name": "non_train_pages",
        "candidate_page_count": 16,
        "candidate_split_counts": {"dev": 8, "test": 8},
        "evaluated_query_count": 24,
        "evaluated_splits": ["dev"],
    }
    assert non_train_report["methods"]["bm25"]["metrics"]["evaluated_queries"] == 24
    assert (
        non_train_report["methods"]["bm25"]["metrics"]["ranked_pages_per_query"] == 16
    )
    assert non_train_report["methods"]["bm25"]["diagnostics"][
        "ranked_page_support"
    ] == {"queries": 24, "min_pages": 16, "max_pages": 16}

    assert all_pages_report["final_test_status"] == "not_run"
    assert all_pages_report["candidate_universe"] == {
        "name": "all_pages",
        "candidate_page_count": 24,
        "candidate_split_counts": {"dev": 8, "test": 8, "train": 8},
        "evaluated_query_count": 24,
        "evaluated_splits": ["dev"],
    }
    assert all_pages_report["methods"]["bm25"]["metrics"]["evaluated_queries"] == 24
    assert all_pages_report["methods"]["bm25"]["metrics"][
        "ranked_pages_per_query"
    ] == 24


def test_report_records_local_stub_neural_provider_without_external_requirements(
    tmp_path: Path,
) -> None:
    config = load_report_config(Path("configs/text-baselines-synthetic-smoke.json"))

    report = run_text_baseline_report(
        config,
        repo_root=Path.cwd(),
        output_path=tmp_path / "neural-text.json",
    )

    neural_text = report["methods"]["neural_text"]
    assert neural_text["external_embeddings_enabled"] is False
    assert neural_text["provider_status"] == {
        "provider": "local_stub",
        "status": "mock_or_local_stub",
        "external_embeddings_enabled": False,
        "network_required": False,
        "gpu_required": False,
        "model_download_required": False,
        "embedding_cache_required": False,
    }
    assert report["boundary"]["network_required"] is False
    assert report["boundary"]["gpu_required"] is False
    assert report["boundary"]["model_download_required"] is False
    assert report["boundary"]["embedding_cache_required"] is False
    assert report["boundary"]["external_embeddings_used"] is False


def test_bm25_neural_rrf_is_distinct_and_gated_on_neural_text(
    tmp_path: Path,
) -> None:
    config = load_report_config(Path("configs/text-baselines-synthetic-smoke.json"))

    report = run_text_baseline_report(
        config,
        repo_root=Path.cwd(),
        output_path=tmp_path / "hybrids.json",
    )

    assert "bm25_lexical_rrf" in report["methods"]
    assert "bm25_neural_rrf" in report["methods"]
    assert report["methods"]["bm25_lexical_rrf"]["fusion"] == {
        "sparse_side_method": "bm25",
        "dense_side_method": "lexical_cosine",
        "rrf_k": 60,
    }
    assert report["methods"]["bm25_neural_rrf"]["fusion"] == {
        "sparse_side_method": "bm25",
        "dense_side_method": "neural_text",
        "rrf_k": 60,
    }

    gated_report = run_text_baseline_report(
        replace(
            config,
            methods={
                "bm25": MethodConfig(enabled=True),
                "lexical_cosine": MethodConfig(enabled=True),
                "bm25_lexical_rrf": MethodConfig(enabled=True),
                "neural_text": MethodConfig(enabled=False),
                "bm25_neural_rrf": MethodConfig(enabled=True),
            },
        ),
        repo_root=Path.cwd(),
        output_path=tmp_path / "gated-hybrid.json",
    )

    assert "neural_text" not in gated_report["methods"]
    assert "bm25_neural_rrf" not in gated_report["methods"]


def test_report_rejects_external_neural_embedding_config(
    tmp_path: Path,
) -> None:
    config = load_report_config(Path("configs/text-baselines-synthetic-smoke.json"))
    output_path = tmp_path / "external-neural.json"

    with pytest.raises(ValueError, match="external neural embeddings"):
        run_text_baseline_report(
            replace(
                config,
                methods={
                    "neural_text": MethodConfig(
                        enabled=True,
                        external_embeddings_enabled=True,
                        provider="local_stub",
                    ),
                },
            ),
            repo_root=Path.cwd(),
            output_path=output_path,
        )

    assert not output_path.exists()


def test_report_rejects_non_local_stub_neural_provider(
    tmp_path: Path,
) -> None:
    config = load_report_config(Path("configs/text-baselines-synthetic-smoke.json"))
    output_path = tmp_path / "external-provider.json"

    with pytest.raises(ValueError, match="only local_stub"):
        run_text_baseline_report(
            replace(
                config,
                methods={
                    "neural_text": MethodConfig(
                        enabled=True,
                        provider="external_provider",
                    ),
                },
            ),
            repo_root=Path.cwd(),
            output_path=output_path,
        )

    assert not output_path.exists()


def test_report_runner_rejects_config_that_evaluates_final_test_split(
    tmp_path: Path,
) -> None:
    bad_config = ReportConfig(
        name="bad-final-test-config",
        pages_manifest=Path("data/synthetic-smoke/pages.jsonl"),
        queries_manifest=Path("data/synthetic-smoke/queries.jsonl"),
        evaluated_splits=("dev", "test"),
        candidate_universe="evaluated_split_pages",
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
