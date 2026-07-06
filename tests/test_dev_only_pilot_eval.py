"""Tests for the Phase 5K dev-only pilot evaluation harness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from visdoc_retrieve.dev_only_pilot_eval import (
    DevOnlyPilotEvalConfigError,
    load_dev_only_pilot_eval_config,
    run_dev_only_pilot_eval,
)


def test_phase_5k_harness_writes_dev_only_schema_and_never_reads_final_test(
    tmp_path: Path,
) -> None:
    config_path = _write_eval_config(tmp_path)

    result = run_dev_only_pilot_eval(
        load_dev_only_pilot_eval_config(config_path),
        repo_root=Path.cwd(),
    )

    assert result["status"] == "dev_only_eval_recorded"
    output_dir = tmp_path / "reports"
    dev_eval = json.loads((output_dir / "phase-5k-dev-only-eval.json").read_text())
    safety = json.loads((output_dir / "phase-5k-safety-check.json").read_text())
    comparison = json.loads(
        (output_dir / "phase-5k-comparison-schema.json").read_text()
    )

    assert dev_eval["schema"] == "training_pilot_phase_5k_dev_only_eval/v1"
    assert dev_eval["scope"] == "dev-only"
    assert dev_eval["final_test_used"] is False
    assert dev_eval["dev_split"]["hard_negative_count"] > 0
    assert dev_eval["dev_split"]["split_values"] == ["dev"]
    assert safety["final_test_files_read"] is False
    assert safety["final_test_metrics_added"] is False
    assert comparison["final_test_used"] is False
    assert comparison["benchmark_improvement_claim"] is False


@pytest.mark.parametrize(
    ("field_name", "bad_path"),
    [
        ("pilot_manifest_path", "reports/final-test/manifest.json"),
        (
            "dev_hard_negatives_path",
            "data/derived/hard_negatives/final-test.jsonl",
        ),
        ("text_baseline_report_path", "reports/final-test/text-baseline.json"),
        ("visual_baseline_report_path", "reports/final-test/visual-baseline.json"),
    ],
)
def test_final_test_input_paths_are_rejected_before_reading(
    tmp_path: Path,
    field_name: str,
    bad_path: str,
) -> None:
    config_path = _write_eval_config(
        tmp_path,
        **{field_name: bad_path},
    )

    with pytest.raises(DevOnlyPilotEvalConfigError, match=field_name):
        load_dev_only_pilot_eval_config(config_path)


def test_missing_adapter_returns_not_available_without_fake_metrics(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(
        Path("reports/training-pilot/phase-5j-adapter-manifest.sanitized.json")
        .read_text(encoding="utf-8")
    )
    manifest["adapter_checkpoint_path"] = ".local/training-pilot/phase-5j/adapters"
    manifest["real_training_result"]["adapter_checkpoint_path"] = (
        ".local/training-pilot/phase-5j/adapters"
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    config_path = _write_eval_config(tmp_path, pilot_manifest_path=manifest_path)
    run_dev_only_pilot_eval(
        load_dev_only_pilot_eval_config(config_path),
        repo_root=Path.cwd(),
    )
    dev_eval = json.loads(
        (tmp_path / "reports" / "phase-5k-dev-only-eval.json").read_text()
    )
    comparison = json.loads(
        (tmp_path / "reports" / "phase-5k-comparison-schema.json").read_text()
    )

    assert dev_eval["tiny_pilot_adapter"]["status"] == "not_available"
    assert dev_eval["tiny_pilot_adapter"]["metrics"] == {
        "mrr": None,
        "recall_at_1": None,
        "recall_at_5": None,
    }
    assert comparison["entries"]["tiny_pilot_adapter"]["status"] == "not_available"
    assert comparison["entries"]["tiny_pilot_adapter"]["metrics"] == {
        "mrr": None,
        "recall_at_1": None,
        "recall_at_5": None,
    }


def test_budget_gates_and_private_path_redaction(tmp_path: Path) -> None:
    over_steps = _write_eval_config(tmp_path, max_steps=21)
    with pytest.raises(DevOnlyPilotEvalConfigError, match="max_steps"):
        load_dev_only_pilot_eval_config(over_steps)

    over_sample = _write_eval_config(tmp_path, sample_limit=9)
    with pytest.raises(DevOnlyPilotEvalConfigError, match="sample_limit"):
        load_dev_only_pilot_eval_config(over_sample)

    private_marker = "REDACTION_TEST_SENTINEL"
    config_path = _write_eval_config(tmp_path, local_model_path=private_marker)
    run_dev_only_pilot_eval(
        load_dev_only_pilot_eval_config(config_path),
        repo_root=Path.cwd(),
    )
    env = json.loads(
        (tmp_path / "reports" / "phase-5k-environment-check.json").read_text()
    )
    assert env["local_model_path_summary"] == {
        "committed_value": "<redacted-local-model-path>",
        "exact_path_committed": False,
        "redacted": True,
    }
    assert private_marker not in (
        tmp_path / "reports" / "phase-5k-environment-check.json"
    ).read_text(encoding="utf-8")


def test_phase_5k_cli_and_existing_cli_surfaces_still_work(tmp_path: Path) -> None:
    config_path = _write_eval_config(tmp_path)
    env = _subprocess_env()

    phase_5k = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.run_dev_only_pilot_eval",
            "--config",
            str(config_path),
        ],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )
    assert phase_5k.returncode == 0, phase_5k.stderr

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


def test_no_forbidden_artifact_files_are_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    forbidden_suffixes = (".safetensors", ".bin", ".ckpt", ".pt", ".pth")
    forbidden_path_fragments = {
        ".worktrees",
        ".codex/skills/openspec-sync-specs",
        "local-models",
        "checkpoints",
        "wandb",
        "runs",
        ".cache",
    }
    for path in tracked:
        path_parts = Path(path).parts
        assert not path.endswith(forbidden_suffixes), path
        assert ".local" not in path_parts, path
        assert not any(part in path for part in forbidden_path_fragments), path


def _write_eval_config(tmp_path: Path, **overrides: object) -> Path:
    output_dir = tmp_path / "reports"
    data: dict[str, object] = {
        "phase": "5K",
        "change": "add-dev-only-pilot-evaluation-harness",
        "pilot_manifest_path": (
            "reports/training-pilot/phase-5j-adapter-manifest.sanitized.json"
        ),
        "dev_hard_negatives_path": "data/derived/hard_negatives/dev.jsonl",
        "text_baseline_report_path": "reports/text-baselines-synthetic-smoke.json",
        "visual_baseline_report_path": "reports/visual-baselines-synthetic-smoke.json",
        "local_model_path": "REDACTION_TEST_SENTINEL",
        "max_steps": 1,
        "sample_limit": 1,
        "final_test_paths": [
            "data/derived/hard_negatives/test.jsonl",
            "data/derived/final-test",
            "reports/final-test",
        ],
        "outputs": {
            "environment_check": str(output_dir / "phase-5k-environment-check.json"),
            "safety_check": str(output_dir / "phase-5k-safety-check.json"),
            "blocked_run_card": str(output_dir / "phase-5k-blocked-run-card.md"),
            "adapter_manifest": str(
                output_dir / "phase-5k-adapter-manifest.sanitized.json"
            ),
            "dev_only_eval": str(output_dir / "phase-5k-dev-only-eval.json"),
            "comparison_schema": str(
                output_dir / "phase-5k-comparison-schema.json"
            ),
            "human_brief": str(
                tmp_path
                / "docs"
                / "human-briefs"
                / "2026-07-06-dev-only-pilot-evaluation.html"
            ),
            "progress_ledger": str(output_dir / "progress-ledger.yaml"),
        },
    }
    data.update(
        {
            key: str(value) if isinstance(value, Path) else value
            for key, value in overrides.items()
        }
    )
    path = tmp_path / "phase-5k-config.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path if not existing else f"{src_path}{os.pathsep}{existing}"
    )
    return env
