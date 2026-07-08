"""Tests for the Phase 6C final-comparison execution dry-run gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from visdoc_retrieve.final_comparison_gate import (
    ArtifactSpec,
    FinalComparisonGateConfigError,
    FinalComparisonGateOutputs,
    build_phase_6c_default_config,
    evaluate_active_openspec_state,
    run_final_comparison_gate,
)


def test_phase_6c_dry_run_schema_and_final_test_path_not_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    final_test_sentinel = tmp_path / "final-test" / "qrels.jsonl"
    final_test_sentinel.parent.mkdir(parents=True)
    final_test_sentinel.write_text("do not read this file", encoding="utf-8")
    original_read_text = Path.read_text

    def guarded_read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == final_test_sentinel:
            raise AssertionError("final-test path was read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    config = _tmp_config(tmp_path, final_test_forbidden_paths=(final_test_sentinel,))

    result = run_final_comparison_gate(
        config,
        repo_root=Path.cwd(),
        active_changes=("add-final-comparison-execution-gate-dry-run",),
    )

    assert result["status"] == "ready_for_phase_6d"
    dry_run = json.loads((tmp_path / "phase-6c-dry-run.json").read_text())
    readiness = (tmp_path / "phase-6c-readiness-report.md").read_text()

    assert dry_run["schema"] == "final_comparison_execution_gate_dry_run/v1"
    assert dry_run["final_test_guard"]["final_test_read"] is False
    assert dry_run["final_comparison_execution"] == "not_executed"
    assert dry_run["benchmark_improvement_claim"] is False
    assert "Phase 6C Final-Comparison Execution Gate Dry-Run" in readiness


def test_active_openspec_state_accepts_only_empty_or_current_change() -> None:
    allowed = "add-final-comparison-execution-gate-dry-run"

    assert evaluate_active_openspec_state((), allowed)["status"] == "pass"
    assert evaluate_active_openspec_state((allowed,), allowed)["status"] == "pass"

    blocked = evaluate_active_openspec_state(("old-change",), allowed)
    assert blocked["status"] == "blocked"
    assert blocked["unexpected_active_changes"] == ["old-change"]


def test_missing_required_artifact_blocks_without_fake_readiness(
    tmp_path: Path,
) -> None:
    config = _tmp_config(
        tmp_path,
        artifacts=(
            ArtifactSpec(
                artifact_id="missing_required_protocol_status",
                path=Path("reports/final-comparison-protocol/missing.json"),
                required=True,
                category="protocol_status",
            ),
        ),
    )

    result = run_final_comparison_gate(
        config,
        repo_root=Path.cwd(),
        active_changes=("add-final-comparison-execution-gate-dry-run",),
    )
    dry_run = json.loads((tmp_path / "phase-6c-dry-run.json").read_text())

    assert result["status"] == "blocked"
    assert "required_artifact_missing" in result["blocked_reasons"]
    assert dry_run["artifact_checks"][0]["status"] == "missing"
    assert dry_run["final_run_readiness"] == "blocked"


def test_missing_optional_artifact_is_missing_not_fabricated(tmp_path: Path) -> None:
    config = _tmp_config(
        tmp_path,
        artifacts=(
            ArtifactSpec(
                artifact_id="optional_longer_dev_adapter",
                path=Path("reports/final-comparison-protocol/not-created.json"),
                required=False,
                category="optional_future_evidence",
            ),
        ),
    )

    result = run_final_comparison_gate(
        config,
        repo_root=Path.cwd(),
        active_changes=("add-final-comparison-execution-gate-dry-run",),
    )
    dry_run = json.loads((tmp_path / "phase-6c-dry-run.json").read_text())

    assert result["status"] == "ready_for_phase_6d"
    assert dry_run["artifact_checks"][0]["status"] == "missing"
    assert dry_run["artifact_checks"][0]["required"] is False
    assert dry_run["planned_runs"][0]["metrics"] is None


def test_claim_checklist_blocks_benchmark_claim_before_final_run(
    tmp_path: Path,
) -> None:
    config = _tmp_config(tmp_path)
    run_final_comparison_gate(
        config,
        repo_root=Path.cwd(),
        active_changes=("add-final-comparison-execution-gate-dry-run",),
    )

    checklist = json.loads((tmp_path / "phase-6c-claim-checklist.json").read_text())

    assert checklist["schema"] == "final_comparison_phase_6c_claim_checklist/v1"
    assert checklist["benchmark_claim_allowed"] is False
    assert checklist["claim_status"] == "blocked_until_phase_6d_final_run"
    assert checklist["checklist"]["final_test_authorized"] is False
    assert checklist["checklist"]["final_comparison_executed"] is False
    assert checklist["checklist"]["reviewer_approval_recorded"] is False


def test_output_path_safety_rejects_private_or_final_test_outputs(
    tmp_path: Path,
) -> None:
    unsafe_outputs = FinalComparisonGateOutputs(
        dry_run=Path(".local/phase-6c.json"),
        readiness_report=tmp_path / "phase-6c-readiness-report.md",
        claim_checklist=tmp_path / "phase-6c-claim-checklist.json",
        human_brief=tmp_path / "phase-6c-human.md",
        progress_ledger=tmp_path / "progress-ledger.yaml",
    )
    config = _tmp_config(tmp_path, outputs=unsafe_outputs)

    with pytest.raises(FinalComparisonGateConfigError, match="unsafe output path"):
        run_final_comparison_gate(
            config,
            repo_root=Path.cwd(),
            active_changes=("add-final-comparison-execution-gate-dry-run",),
        )


def test_phase_6c_cli_and_existing_cli_surfaces_still_work(tmp_path: Path) -> None:
    env = _subprocess_env()
    phase_6c = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.run_final_comparison_gate",
            "--repo-root",
            ".",
            "--dry-run-output",
            str(tmp_path / "phase-6c-dry-run.json"),
            "--readiness-report-output",
            str(tmp_path / "phase-6c-readiness-report.md"),
            "--claim-checklist-output",
            str(tmp_path / "phase-6c-claim-checklist.json"),
            "--human-brief-output",
            str(tmp_path / "phase-6c-human.md"),
            "--progress-ledger-output",
            str(tmp_path / "progress-ledger.yaml"),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )
    assert phase_6c.returncode == 0, phase_6c.stderr

    commands = [
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.run_mvp",
            "--config",
            "configs/mvp.json",
        ],
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.mine_hard_negatives",
            "--config",
            "configs/hard_negatives.json",
        ],
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.train_lora_dry_run",
            "--config",
            "configs/train_lora_dry_run.json",
        ],
    ]
    for command in commands:
        completed = subprocess.run(
            command,
            check=False,
            env=env,
            text=True,
            capture_output=True,
        )
        assert completed.returncode == 0, completed.stderr

    blocked = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.train_lora_pilot",
            "--config",
            "configs/train_lora_pilot.local.example.json",
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )
    assert blocked.returncode == 2


def _tmp_config(
    tmp_path: Path,
    *,
    artifacts: tuple[ArtifactSpec, ...] | None = None,
    outputs: FinalComparisonGateOutputs | None = None,
    final_test_forbidden_paths: tuple[Path, ...] = (),
) -> object:
    config = build_phase_6c_default_config()
    return config.with_overrides(
        artifacts=artifacts,
        outputs=outputs
        or FinalComparisonGateOutputs(
            dry_run=tmp_path / "phase-6c-dry-run.json",
            readiness_report=tmp_path / "phase-6c-readiness-report.md",
            claim_checklist=tmp_path / "phase-6c-claim-checklist.json",
            human_brief=tmp_path / "phase-6c-human.md",
            progress_ledger=tmp_path / "progress-ledger.yaml",
        ),
        final_test_forbidden_paths=final_test_forbidden_paths,
    )


def _subprocess_env() -> dict[str, str]:
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = "src"
    return env
