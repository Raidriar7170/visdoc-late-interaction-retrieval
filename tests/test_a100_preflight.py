"""Tests for Phase 5E A100 setup/preflight evidence."""

from __future__ import annotations

import json
from pathlib import Path

from visdoc_retrieve import a100_preflight

DEPENDENCY_INSTALL_ATTEMPT = "stopped_before_large_torch_wheel_download"


def test_missing_dependency_and_model_path_block_without_training() -> None:
    evidence = a100_preflight.build_phase_5e_preflight_evidence(
        _observation(
            module_available={"colpali_engine": False},
            model_path={"provided": False},
        ),
        report_timestamp_utc="2026-07-02T00:00:00Z",
    )

    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert blocker_codes == {"optional_dependency_missing", "needs_user_model_path"}

    safety = evidence["safety"]
    assert safety["training_launched"] is False
    assert safety["model_download_executed"] is False
    assert safety["final_test_used"] is False
    assert safety["adapter_checkpoint_created"] is False
    assert safety["benchmark_improvement_claim"] is False
    assert evidence["dependency_setup"] == {
        "isolated_env_under_allowed_root": True,
        "colpali_engine_install_attempt": DEPENDENCY_INSTALL_ATTEMPT,
    }


def test_ready_when_checkout_cuda_dependencies_and_model_path_exist() -> None:
    evidence = a100_preflight.build_phase_5e_preflight_evidence(
        _observation(
            model_path={
                "provided": True,
                "exists": True,
                "path": "/mnt/data/minghongsun/models/private-colqwen",
            },
        ),
        report_timestamp_utc="2026-07-02T00:00:00Z",
    )

    assert evidence["status"] == "preflight_ready"
    assert evidence["blocked_reasons"] == []
    assert evidence["cuda"]["safe_idle_gpu_candidates"] == [3, 4]
    assert evidence["local_model_path_summary"] == {
        "provided": True,
        "exists": True,
        "redacted": True,
        "exact_path_committed": False,
        "path_location": "under_allowed_root",
    }


def test_preflight_evidence_does_not_commit_sensitive_remote_details() -> None:
    evidence = a100_preflight.build_phase_5e_preflight_evidence(
        _observation(
            checkout={
                "branch": "main",
                "clean": True,
                "exists": True,
                "git_inspected": True,
                "head_commit": "abc123",
                "origin_main_commit": "abc123",
                "path": "/mnt/data/minghongsun/visdoc-late-interaction-retrieval",
                "raw_remote": "private-host-marker pid 12345",
            },
            model_path={
                "provided": True,
                "exists": True,
                "path": "/mnt/data/minghongsun/secret/models/colpali",
            },
        ),
        report_timestamp_utc="2026-07-02T00:00:00Z",
    )

    evidence_text = json.dumps(evidence, sort_keys=True)
    assert "private-host-marker" not in evidence_text
    assert "12345" not in evidence_text
    assert "/mnt/data/minghongsun/secret/models/colpali" not in evidence_text
    assert evidence["remote"]["host_ip_committed"] is False
    assert evidence["remote"]["process_ids_committed"] is False
    assert evidence["local_model_path_summary"]["exact_path_committed"] is False


def test_cli_writes_environment_safety_and_run_card(tmp_path: Path) -> None:
    observation_path = tmp_path / "observation.json"
    environment_path = tmp_path / "environment.json"
    safety_path = tmp_path / "safety.json"
    run_card_path = tmp_path / "run-card.md"
    observation_path.write_text(
        json.dumps(_observation(model_path={"provided": False})),
        encoding="utf-8",
    )

    exit_code = a100_preflight.main(
        [
            "--input",
            str(observation_path),
            "--environment-check",
            str(environment_path),
            "--safety-check",
            str(safety_path),
            "--run-card",
            str(run_card_path),
            "--timestamp-utc",
            "2026-07-02T00:00:00Z",
        ]
    )

    assert exit_code == 0
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    safety = json.loads(safety_path.read_text(encoding="utf-8"))
    run_card = run_card_path.read_text(encoding="utf-8")
    assert environment["schema"] == "phase_5e_a100_real_training_preflight/v1"
    assert safety["schema"] == "phase_5e_a100_preflight_safety/v1"
    assert "Boundary: setup/preflight only; real training was not launched." in run_card


def _observation(
    *,
    checkout: dict[str, object] | None = None,
    module_available: dict[str, bool] | None = None,
    model_path: dict[str, object] | None = None,
) -> dict[str, object]:
    modules = {
        "torch": True,
        "transformers": True,
        "peft": True,
        "colpali_engine": True,
    }
    if module_available is not None:
        modules.update(module_available)
    return {
        "remote": {
            "storage_dir_exists": True,
            "storage_dir_writable": True,
        },
        "checkout": checkout
        or {
            "branch": "main",
            "clean": True,
            "exists": True,
            "git_inspected": True,
            "head_commit": "abc123",
            "origin_main_commit": "abc123",
            "path": "/mnt/data/minghongsun/visdoc-late-interaction-retrieval",
        },
        "runtime": {
            "python": "base-conda-python",
            "module_available": modules,
        },
        "dependency_setup": {
            "isolated_env_under_allowed_root": True,
            "colpali_engine_install_attempt": DEPENDENCY_INSTALL_ATTEMPT,
        },
        "cuda": {
            "available": True,
            "device_count": 8,
        },
        "gpus": [
            {
                "index": 0,
                "name": "NVIDIA A100-SXM4-80GB",
                "memory_used_mib": 19534,
                "utilization_gpu_percent": 0,
            },
            {
                "index": 3,
                "name": "NVIDIA A100-SXM4-80GB",
                "memory_used_mib": 7,
                "utilization_gpu_percent": 0,
            },
            {
                "index": 4,
                "name": "NVIDIA A100-SXM4-80GB",
                "memory_used_mib": 7,
                "utilization_gpu_percent": 0,
            },
        ],
        "model_path": model_path
        or {
            "provided": True,
            "exists": True,
            "path": "/mnt/data/minghongsun/models/private-colpali",
        },
    }
