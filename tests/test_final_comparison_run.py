"""Tests for the Phase 6D one-time frozen final comparison."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from visdoc_retrieve.final_comparison_run import (
    FinalComparisonRunConfigError,
    FinalComparisonRunOutputs,
    build_phase_6d_default_config,
    run_final_comparison,
)


def test_phase_6d_final_run_manifest_metrics_and_pledge_schema(
    tmp_path: Path,
) -> None:
    config = _tmp_config(tmp_path)

    result = run_final_comparison(
        config,
        repo_root=Path.cwd(),
        active_changes=("run-one-time-frozen-final-comparison",),
    )

    assert result["status"] == "final_comparison_complete"
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    checklist = json.loads((tmp_path / "claim-checklist.json").read_text())
    pledge = (tmp_path / "no-retune-pledge.md").read_text()

    assert manifest["schema"] == "final_comparison_run_manifest/v1"
    assert manifest["phase"] == "6D"
    assert manifest["final_test"]["read"] is True
    assert manifest["final_test"]["split"] == "test"
    assert manifest["no_retune_pledge"]["accepted"] is True
    assert manifest["training"] == "not_executed"
    assert manifest["tuning_after_final"] == "forbidden"
    assert manifest["a100_or_gpu_used"] is False
    assert manifest["model_download"] == "not_executed"
    assert "sha256" in manifest["protocol"]
    assert "sha256" in manifest["candidate_universe"]
    assert "sha256" in manifest["final_test"]

    assert metrics["schema"] == "final_comparison_metrics/v1"
    assert metrics["split_scope"] == "final_test"
    assert metrics["candidate_universe"]["name"] == "evaluated_split_pages"
    assert metrics["candidate_universe"]["candidate_page_count"] == 8
    assert metrics["candidate_universe"]["evaluated_query_count"] == 24
    assert sorted(metrics["systems"]) == [
        "bm25",
        "bm25_lexical_rrf",
        "lexical_cosine",
        "mock_visual",
        "tiny_lora_adapter",
        "zero_shot_visual_backend",
    ]
    for method_id in ("bm25", "lexical_cosine", "bm25_lexical_rrf", "mock_visual"):
        row = metrics["systems"][method_id]
        assert row["status"] == "final_benchmark"
        assert row["final_test_used"] is True
        assert row["overall"]["support"] == 24
        assert row["overall"]["metrics"]["evaluated_queries"] == 24
        assert row["overall"]["metrics"]["ranked_pages_per_query"] == 8
        for metric_name in ("recall_at_1", "recall_at_5", "mrr", "ndcg_at_10"):
            assert metric_name in row["overall"]["metrics"]

    assert metrics["systems"]["zero_shot_visual_backend"]["status"] == (
        "not_available"
    )
    assert metrics["systems"]["zero_shot_visual_backend"]["metrics"] is None
    assert metrics["systems"]["tiny_lora_adapter"]["status"] == "not_available"
    assert metrics["systems"]["tiny_lora_adapter"]["metrics"] is None

    assert checklist["schema"] == "final_comparison_claim_checklist/v1"
    assert checklist["benchmark_claim_allowed"] is False
    assert checklist["claim_status"] == "no_clear_improvement_claim"
    assert checklist["checklist"]["final_test_read"] is True
    assert checklist["checklist"]["final_comparison_executed"] is True
    assert checklist["checklist"]["dev_only_not_presented_as_final"] is True
    assert "No tuning, retrieval-pipeline changes" in pledge


def test_phase_6d_subset_metrics_keep_null_for_zero_support(tmp_path: Path) -> None:
    run_final_comparison(
        _tmp_config(tmp_path),
        repo_root=Path.cwd(),
        active_changes=("run-one-time-frozen-final-comparison",),
    )

    metrics = json.loads((tmp_path / "metrics.json").read_text())
    for row in metrics["systems"].values():
        if row["status"] != "final_benchmark":
            continue
        subsets = row["by_query_type"]
        assert set(subsets) == {"figure", "layout", "ocr_failure", "table", "text"}
        for subset in subsets.values():
            if subset["support"] == 0:
                assert subset["metrics"] is None
            else:
                assert subset["metrics"]["evaluated_queries"] == subset["support"]


def test_phase_6d_default_outputs_cannot_run_twice_without_override(
    tmp_path: Path,
) -> None:
    config = _tmp_config(tmp_path)
    run_final_comparison(
        config,
        repo_root=Path.cwd(),
        active_changes=("run-one-time-frozen-final-comparison",),
    )

    with pytest.raises(FinalComparisonRunConfigError, match="already exists"):
        run_final_comparison(
            config,
            repo_root=Path.cwd(),
            active_changes=("run-one-time-frozen-final-comparison",),
        )

    rerun = run_final_comparison(
        config.with_overrides(allow_rerun=True),
        repo_root=Path.cwd(),
        active_changes=("run-one-time-frozen-final-comparison",),
    )
    assert rerun["status"] == "final_comparison_complete"


def test_phase_6d_cli_runs_with_temp_outputs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.run_final_comparison",
            "--repo-root",
            ".",
            "--manifest-output",
            str(tmp_path / "manifest.json"),
            "--metrics-output",
            str(tmp_path / "metrics.json"),
            "--rankings-output",
            str(tmp_path / "rankings.csv"),
            "--report-output",
            str(tmp_path / "report.md"),
            "--claim-checklist-output",
            str(tmp_path / "claim-checklist.json"),
            "--no-retune-pledge-output",
            str(tmp_path / "no-retune-pledge.md"),
            "--human-brief-output",
            str(tmp_path / "human-brief.md"),
            "--progress-ledger-output",
            str(tmp_path / "progress-ledger.yaml"),
            "--allow-rerun",
        ],
        check=False,
        env=_subprocess_env(),
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "metrics.json").is_file()
    assert (tmp_path / "rankings.csv").is_file()


def _tmp_config(tmp_path: Path) -> object:
    return build_phase_6d_default_config().with_overrides(
        outputs=FinalComparisonRunOutputs(
            manifest=tmp_path / "manifest.json",
            metrics=tmp_path / "metrics.json",
            rankings=tmp_path / "rankings.csv",
            report=tmp_path / "report.md",
            claim_checklist=tmp_path / "claim-checklist.json",
            no_retune_pledge=tmp_path / "no-retune-pledge.md",
            human_brief=tmp_path / "human-brief.md",
            progress_ledger=tmp_path / "progress-ledger.yaml",
        )
    )


def _subprocess_env() -> dict[str, str]:
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = "src"
    return env
