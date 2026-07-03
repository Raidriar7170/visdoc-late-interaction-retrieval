"""Tests for Phase 5E/5F A100 setup and runtime-gate evidence."""

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
    sensitive_host_marker = "host-" + "should-not-appear"
    sensitive_process_marker = "pid-" + "should-not-appear"
    exact_model_path = "/".join(
        (
            "",
            "mnt",
            "data",
            "minghongsun",
            "sensitive-model-root",
            "models",
            "colpali",
        )
    )
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
                "raw_remote": f"{sensitive_host_marker} {sensitive_process_marker}",
            },
            model_path={
                "provided": True,
                "exists": True,
                "path": exact_model_path,
            },
        ),
        report_timestamp_utc="2026-07-02T00:00:00Z",
    )

    evidence_text = json.dumps(evidence, sort_keys=True)
    assert sensitive_host_marker not in evidence_text
    assert sensitive_process_marker not in evidence_text
    assert exact_model_path not in evidence_text
    assert evidence["remote"]["host_ip_committed"] is False
    assert evidence["remote"]["process_ids_committed"] is False
    assert evidence["local_model_path_summary"]["exact_path_committed"] is False


def test_phase_5f_missing_dependency_and_model_path_block_runtime_gates() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            module_available={"colpali_engine": False},
            model_path={"provided": False},
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["schema"] == "phase_5f_a100_runtime_gates/v1"
    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert blocker_codes == {"optional_dependency_missing", "needs_user_model_path"}

    gates = evidence["runtime_gates"]
    assert gates["dependency_importability"]["ready"] is False
    assert gates["dependency_importability"]["missing_optional_modules"] == [
        "colpali_engine"
    ]
    assert gates["local_model_path"]["ready"] is False
    assert gates["local_model_path"]["exact_local_model_path_required"] is True

    safety = evidence["safety"]
    assert safety["training_launched"] is False
    assert safety["model_download_executed"] is False
    assert safety["network_used_for_model_resolution"] is False
    assert safety["final_test_used"] is False
    assert safety["adapter_checkpoint_created"] is False
    assert safety["benchmark_improvement_claim"] is False


def test_phase_5f_missing_exact_model_path_needs_user_input() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(model_path={"provided": False}),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "needs_user_input"
    assert evidence["user_input_required"] is True
    assert [reason["code"] for reason in evidence["blocked_reasons"]] == [
        "needs_user_model_path"
    ]
    assert evidence["runtime_gates"]["local_model_path"] == {
        "ready": False,
        "exact_local_model_path_required": True,
        "provided": False,
        "exists": False,
        "redacted": True,
        "exact_path_committed": False,
        "path_location": "not_provided",
        "a100_readable": False,
        "shape_markers_present": False,
        "model_shape_ready": False,
    }


def test_phase_5f_runtime_ready_keeps_training_side_effects_false() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            model_path={
                "provided": True,
                "exists": True,
                "path": "/mnt/data/minghongsun/models/private-colqwen",
                "expected_file_markers_present": True,
                "a100_readable": True,
            },
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "runtime_ready"
    assert evidence["blocked_reasons"] == []
    assert evidence["runtime_gates"]["allowed_root_placement"] == {
        "ready": True,
        "isolated_env_under_allowed_root": True,
        "cache_dirs_under_allowed_root": True,
    }
    assert evidence["runtime_gates"]["dependency_importability"]["ready"] is True
    assert evidence["runtime_gates"]["cuda_and_gpu"]["ready"] is True
    assert evidence["runtime_gates"]["local_model_path"] == {
        "ready": True,
        "exact_local_model_path_required": True,
        "provided": True,
        "exists": True,
        "redacted": True,
        "exact_path_committed": False,
        "path_location": "under_allowed_root",
        "a100_readable": True,
        "shape_markers_present": True,
        "model_shape_ready": True,
    }
    assert evidence["safety"]["training_launched"] is False
    assert evidence["safety"]["model_download_executed"] is False
    assert evidence["safety"]["adapter_checkpoint_created"] is False
    assert evidence["safety"]["real_training_success_claim"] is False


def test_phase_5f_under_allowed_root_path_still_needs_readability_signal() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            model_path={
                "provided": True,
                "exists": True,
                "path": "/mnt/data/minghongsun/models/private-colqwen",
                "expected_file_markers_present": True,
            },
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert "local_model_path_not_a100_readable" in blocker_codes
    assert evidence["runtime_gates"]["local_model_path"] == {
        "ready": False,
        "exact_local_model_path_required": True,
        "provided": True,
        "exists": True,
        "redacted": True,
        "exact_path_committed": False,
        "path_location": "under_allowed_root",
        "a100_readable": False,
        "shape_markers_present": True,
        "model_shape_ready": True,
    }


def test_phase_5f_mac_local_model_path_is_not_runtime_ready() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            model_path={
                "provided": True,
                "exists": True,
                "path": "/Users/example/models/private-colqwen",
                "expected_file_markers_present": True,
            },
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert "local_model_path_not_a100_readable" in blocker_codes
    assert evidence["runtime_gates"]["local_model_path"]["ready"] is False


def test_phase_5f_explicit_not_a100_readable_overrides_allowed_root_path() -> None:
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            model_path={
                "provided": True,
                "exists": True,
                "path": "/mnt/data/minghongsun/models/private-colqwen",
                "expected_file_markers_present": True,
                "a100_readable": False,
            },
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert "local_model_path_not_a100_readable" in blocker_codes
    assert evidence["runtime_gates"]["local_model_path"]["a100_readable"] is False
    assert evidence["runtime_gates"]["local_model_path"]["ready"] is False


def test_phase_5f_runtime_placement_gates_block_outside_root() -> None:
    observation = _phase_5f_observation(
        model_path={
            "provided": True,
            "exists": True,
            "path": "/mnt/data/minghongsun/models/private-colqwen",
            "expected_file_markers_present": True,
            "a100_readable": True,
        },
    )
    dependency_setup = observation["dependency_setup"]
    assert isinstance(dependency_setup, dict)
    dependency_setup["isolated_env_under_allowed_root"] = False
    dependency_setup["cache_dirs_under_allowed_root"] = False

    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        observation,
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    assert evidence["status"] == "blocked"
    blocker_codes = {reason["code"] for reason in evidence["blocked_reasons"]}
    assert "isolated_runtime_env_outside_allowed_root" in blocker_codes
    assert "runtime_cache_outside_allowed_root" in blocker_codes
    assert evidence["runtime_gates"]["allowed_root_placement"] == {
        "ready": False,
        "isolated_env_under_allowed_root": False,
        "cache_dirs_under_allowed_root": False,
    }


def test_phase_5f_redacts_private_paths_ips_and_process_ids() -> None:
    sensitive_ipv4 = ".".join(("10", "2", "3", "4"))
    sensitive_host_marker = "host-" + "should-not-appear"
    sensitive_process_marker = "pid-" + "should-not-appear"
    exact_model_path = "/".join(
        (
            "",
            "mnt",
            "data",
            "minghongsun",
            "sensitive-model-root",
            "models",
            "colpali",
        )
    )
    evidence = a100_preflight.build_phase_5f_runtime_gate_evidence(
        _phase_5f_observation(
            checkout={
                "branch": "main",
                "clean": True,
                "exists": True,
                "git_inspected": True,
                "head_commit": "abc123",
                "origin_main_commit": "abc123",
                "path": "/mnt/data/minghongsun/visdoc-late-interaction-retrieval",
                "raw_remote": (
                    f"{sensitive_host_marker} "
                    f"{sensitive_ipv4} "
                    f"{sensitive_process_marker}"
                ),
            },
            model_path={
                "provided": True,
                "exists": True,
                "path": exact_model_path,
                "expected_file_markers_present": True,
            },
        ),
        report_timestamp_utc="2026-07-03T00:00:00Z",
    )

    evidence_text = json.dumps(evidence, sort_keys=True)
    assert exact_model_path not in evidence_text
    assert sensitive_host_marker not in evidence_text
    assert sensitive_ipv4 not in evidence_text
    assert sensitive_process_marker not in evidence_text
    local_model_path_gate = evidence["runtime_gates"]["local_model_path"]
    assert local_model_path_gate["exact_path_committed"] is False
    assert evidence["remote"]["host_ip_committed"] is False
    assert evidence["remote"]["process_ids_committed"] is False


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


def test_cli_writes_phase_5f_runtime_gate_outputs(tmp_path: Path) -> None:
    observation_path = tmp_path / "observation.json"
    environment_path = tmp_path / "environment.json"
    safety_path = tmp_path / "safety.json"
    run_card_path = tmp_path / "run-card.md"
    observation_path.write_text(
        json.dumps(
            _phase_5f_observation(
                module_available={"colpali_engine": False},
                model_path={"provided": False},
            )
        ),
        encoding="utf-8",
    )

    exit_code = a100_preflight.main(
        [
            "--phase",
            "5f",
            "--input",
            str(observation_path),
            "--environment-check",
            str(environment_path),
            "--safety-check",
            str(safety_path),
            "--run-card",
            str(run_card_path),
            "--timestamp-utc",
            "2026-07-03T00:00:00Z",
        ]
    )

    assert exit_code == 0
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    safety = json.loads(safety_path.read_text(encoding="utf-8"))
    run_card = run_card_path.read_text(encoding="utf-8")
    assert environment["schema"] == "phase_5f_a100_runtime_gates/v1"
    assert environment["status"] == "blocked"
    assert safety["schema"] == "phase_5f_a100_runtime_gate_safety/v1"
    assert "Boundary: runtime-gate materialization only" in run_card


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


def _phase_5f_observation(
    *,
    checkout: dict[str, object] | None = None,
    module_available: dict[str, bool] | None = None,
    model_path: dict[str, object] | None = None,
) -> dict[str, object]:
    observation = _observation(
        checkout=checkout,
        module_available=module_available,
        model_path=model_path,
    )
    dependency_setup = observation["dependency_setup"]
    assert isinstance(dependency_setup, dict)
    dependency_setup["cache_dirs_under_allowed_root"] = True
    model_summary = observation["model_path"]
    assert isinstance(model_summary, dict)
    if model_summary.get("provided") is True:
        model_summary.setdefault("expected_file_markers_present", True)
    return observation
