"""Phase 5E/5F A100 remote setup and runtime-gate evidence helpers."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, cast

ALLOWED_REMOTE_ROOT = PurePosixPath("/mnt/data/minghongsun")
EXPECTED_REMOTE_REPO = ALLOWED_REMOTE_ROOT / "visdoc-late-interaction-retrieval"
REQUIRED_OPTIONAL_MODULES = ("torch", "transformers", "peft", "colpali_engine")
IDLE_GPU_MAX_MEMORY_MIB = 1024
IDLE_GPU_MAX_UTILIZATION_PERCENT = 5
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def build_phase_5e_preflight_evidence(
    observation: Mapping[str, Any],
    *,
    report_timestamp_utc: str | None = None,
) -> dict[str, object]:
    """Build public-safe Phase 5E evidence from structured remote observations."""

    timestamp = (
        report_timestamp_utc or datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    remote = _mapping(observation.get("remote"))
    checkout = _mapping(observation.get("checkout"))
    runtime = _mapping(observation.get("runtime"))
    cuda = _mapping(observation.get("cuda"))
    model_path = _mapping(observation.get("model_path"))
    dependency_setup = _mapping(observation.get("dependency_setup"))
    gpus = [_mapping(item) for item in _sequence(observation.get("gpus"))]

    blockers: list[dict[str, object]] = []
    allowed_root = str(ALLOWED_REMOTE_ROOT)
    expected_repo = str(EXPECTED_REMOTE_REPO)

    if remote.get("storage_dir_exists") is not True:
        _add_blocker(
            blockers,
            "allowed_storage_missing",
            "Allowed remote storage root is unavailable.",
        )
    if remote.get("storage_dir_writable") is not True:
        _add_blocker(
            blockers,
            "allowed_storage_not_writable",
            "Allowed remote storage root is not writable.",
        )

    checkout_path = str(checkout.get("path", expected_repo))
    checkout_under_allowed_root = _is_under_allowed_root(checkout_path)
    if not checkout_under_allowed_root:
        _add_blocker(
            blockers,
            "remote_checkout_outside_allowed_root",
            "Remote checkout path is outside the allowed storage root.",
        )
    if checkout.get("exists") is not True:
        _add_blocker(
            blockers,
            "remote_checkout_missing",
            "Remote VisDoc checkout is unavailable.",
        )
    elif checkout.get("git_inspected") is not True:
        _add_blocker(
            blockers,
            "remote_checkout_not_git",
            "Remote checkout Git metadata was not inspectable.",
        )
    elif checkout.get("clean") is not True:
        _add_blocker(blockers, "remote_checkout_dirty", "Remote checkout is not clean.")

    module_available = {
        name: bool(_mapping(runtime.get("module_available")).get(name))
        for name in REQUIRED_OPTIONAL_MODULES
    }
    missing_modules = [
        name for name, available in module_available.items() if not available
    ]
    if missing_modules:
        blockers.append(
            {
                "code": "optional_dependency_missing",
                "message": (
                    "One or more optional real-training dependencies are missing."
                ),
                "dependencies": missing_modules,
            }
        )

    cuda_available = cuda.get("available") is True
    if not cuda_available:
        _add_blocker(
            blockers,
            "cuda_unavailable",
            "CUDA is not available to the checked Python runtime.",
        )

    safe_idle_gpu_candidates = _safe_idle_gpu_candidates(gpus)
    if cuda_available and not safe_idle_gpu_candidates:
        _add_blocker(
            blockers, "no_safe_idle_gpu", "No clearly idle GPU candidate was found."
        )

    model_provided = model_path.get("provided") is True
    model_exists = model_path.get("exists") is True
    if not model_provided:
        _add_blocker(
            blockers,
            "needs_user_model_path",
            "No exact local ColPali / ColQwen model path was available.",
        )
    elif not model_exists:
        _add_blocker(
            blockers,
            "missing_local_model_path",
            "The provided local model path does not exist on the remote host.",
        )

    status = _overall_status(blockers)
    safety = _safety_summary(status=status)
    evidence: dict[str, object] = {
        "schema": "phase_5e_a100_real_training_preflight/v1",
        "status": status,
        "report_timestamp_utc": timestamp,
        "remote": {
            "access_method": "ssh_alias",
            "allowed_storage_root": allowed_root,
            "storage_dir_exists": remote.get("storage_dir_exists") is True,
            "storage_dir_writable": remote.get("storage_dir_writable") is True,
            "host_ip_committed": False,
            "ssh_details_committed": False,
            "process_ids_committed": False,
        },
        "checkout": {
            "expected_project_root": expected_repo,
            "path_under_allowed_root": checkout_under_allowed_root,
            "exists": checkout.get("exists") is True,
            "git_inspected": checkout.get("git_inspected") is True,
            "branch": _optional_public_str(checkout.get("branch")),
            "head_commit": _optional_public_str(checkout.get("head_commit")),
            "origin_main_commit": _optional_public_str(
                checkout.get("origin_main_commit")
            ),
            "clean": checkout.get("clean") is True,
        },
        "runtime": {
            "python": _optional_public_str(runtime.get("python")),
            "module_available": module_available,
        },
        "dependency_setup": {
            "isolated_env_under_allowed_root": dependency_setup.get(
                "isolated_env_under_allowed_root"
            )
            is True,
            "colpali_engine_install_attempt": _optional_public_str(
                dependency_setup.get("colpali_engine_install_attempt")
            ),
        },
        "cuda": {
            "available": cuda_available,
            "device_count": _optional_int(cuda.get("device_count")),
            "gpu_model_summary": _gpu_model_summary(gpus),
            "safe_idle_gpu_candidates": safe_idle_gpu_candidates,
            "busy_gpu_count": _busy_gpu_count(gpus),
        },
        "local_model_path_summary": {
            "provided": model_provided,
            "exists": model_exists if model_provided else False,
            "redacted": True,
            "exact_path_committed": False,
            "path_location": _model_path_location(model_path),
        },
        "blocked_reasons": blockers,
        "user_input_required": any(
            reason["code"] in {"needs_user_model_path", "missing_local_model_path"}
            for reason in blockers
        ),
        "safety": safety,
    }
    return evidence


def write_phase_5e_outputs(
    observation: Mapping[str, Any],
    *,
    environment_check_path: Path,
    safety_check_path: Path,
    run_card_path: Path,
    report_timestamp_utc: str | None = None,
) -> dict[str, object]:
    """Write Phase 5E JSON and run-card outputs."""

    evidence = build_phase_5e_preflight_evidence(
        observation,
        report_timestamp_utc=report_timestamp_utc,
    )
    _write_json(environment_check_path, evidence)
    _write_json(safety_check_path, cast(dict[str, object], evidence["safety"]))
    _write_text(run_card_path, render_phase_5e_run_card(evidence))
    return evidence


def build_phase_5f_runtime_gate_evidence(
    observation: Mapping[str, Any],
    *,
    report_timestamp_utc: str | None = None,
) -> dict[str, object]:
    """Build public-safe Phase 5F runtime-gate evidence."""

    evidence = build_phase_5e_preflight_evidence(
        observation,
        report_timestamp_utc=report_timestamp_utc,
    )
    dependency_setup = _mapping(observation.get("dependency_setup"))
    model_path = _mapping(observation.get("model_path"))

    blockers = [
        dict(reason)
        for reason in cast(Sequence[Mapping[str, object]], evidence["blocked_reasons"])
    ]
    isolated_env_under_allowed_root = (
        dependency_setup.get("isolated_env_under_allowed_root") is True
    )
    cache_dirs_under_allowed_root = (
        dependency_setup.get("cache_dirs_under_allowed_root") is True
    )
    if not isolated_env_under_allowed_root:
        _add_blocker(
            blockers,
            "isolated_runtime_env_outside_allowed_root",
            "The checked runtime environment is not isolated under the allowed root.",
        )
    if not cache_dirs_under_allowed_root:
        _add_blocker(
            blockers,
            "runtime_cache_outside_allowed_root",
            "Runtime cache directories are not confirmed under the allowed root.",
        )

    model_provided = model_path.get("provided") is True
    model_exists = model_path.get("exists") is True
    shape_markers_present = (
        model_provided
        and model_exists
        and model_path.get("expected_file_markers_present") is True
    )
    model_path_a100_readable = _model_path_a100_readable(model_path)
    if model_provided and model_exists and not shape_markers_present:
        _add_blocker(
            blockers,
            "model_shape_markers_missing",
            "The provided local model path does not have expected model-file markers.",
        )
    if model_provided and model_exists and not model_path_a100_readable:
        _add_blocker(
            blockers,
            "local_model_path_not_a100_readable",
            "The provided local model path is not confirmed readable on the A100 host.",
        )

    cuda = cast(Mapping[str, object], evidence["cuda"])
    runtime = cast(Mapping[str, object], evidence["runtime"])
    module_available = cast(Mapping[str, object], runtime["module_available"])
    missing_modules = [
        name
        for name in REQUIRED_OPTIONAL_MODULES
        if module_available.get(name) is False
    ]
    local_model_path_gate = {
        "ready": (
            model_provided
            and model_exists
            and shape_markers_present
            and model_path_a100_readable
        ),
        "exact_local_model_path_required": True,
        "provided": model_provided,
        "exists": model_exists if model_provided else False,
        "redacted": True,
        "exact_path_committed": False,
        "path_location": _model_path_location(model_path),
        "a100_readable": model_path_a100_readable,
        "shape_markers_present": shape_markers_present,
        "model_shape_ready": shape_markers_present,
    }
    runtime_gates = {
        "dependency_importability": {
            "ready": not missing_modules,
            "required_optional_modules": list(REQUIRED_OPTIONAL_MODULES),
            "missing_optional_modules": missing_modules,
        },
        "allowed_root_placement": {
            "ready": isolated_env_under_allowed_root and cache_dirs_under_allowed_root,
            "isolated_env_under_allowed_root": isolated_env_under_allowed_root,
            "cache_dirs_under_allowed_root": cache_dirs_under_allowed_root,
        },
        "cuda_and_gpu": {
            "ready": bool(cuda["available"]) and bool(cuda["safe_idle_gpu_candidates"]),
            "cuda_available": bool(cuda["available"]),
            "safe_idle_gpu_candidates": cuda["safe_idle_gpu_candidates"],
        },
        "local_model_path": local_model_path_gate,
    }
    status = _phase_5f_status(blockers)
    safety = _safety_summary(status=status)
    safety["schema"] = "phase_5f_a100_runtime_gate_safety/v1"

    evidence.update(
        {
            "schema": "phase_5f_a100_runtime_gates/v1",
            "status": status,
            "dependency_setup": {
                "isolated_env_under_allowed_root": isolated_env_under_allowed_root,
                "cache_dirs_under_allowed_root": cache_dirs_under_allowed_root,
                "colpali_engine_install_attempt": _optional_public_str(
                    dependency_setup.get("colpali_engine_install_attempt")
                ),
            },
            "local_model_path_summary": local_model_path_gate,
            "runtime_gates": runtime_gates,
            "blocked_reasons": blockers,
            "user_input_required": any(
                reason["code"] in {"needs_user_model_path", "missing_local_model_path"}
                for reason in blockers
            ),
            "safety": safety,
        }
    )
    return evidence


def write_phase_5f_outputs(
    observation: Mapping[str, Any],
    *,
    environment_check_path: Path,
    safety_check_path: Path,
    run_card_path: Path,
    report_timestamp_utc: str | None = None,
) -> dict[str, object]:
    """Write Phase 5F JSON and run-card outputs."""

    evidence = build_phase_5f_runtime_gate_evidence(
        observation,
        report_timestamp_utc=report_timestamp_utc,
    )
    _write_json(environment_check_path, evidence)
    _write_json(safety_check_path, cast(dict[str, object], evidence["safety"]))
    _write_text(run_card_path, render_phase_5f_run_card(evidence))
    return evidence


def render_phase_5e_run_card(evidence: Mapping[str, object]) -> str:
    """Render a compact public-safe Markdown run card."""

    status = str(evidence["status"])
    blockers = cast(Sequence[Mapping[str, object]], evidence["blocked_reasons"])
    cuda = cast(Mapping[str, object], evidence["cuda"])
    runtime = cast(Mapping[str, object], evidence["runtime"])
    model_summary = cast(Mapping[str, object], evidence["local_model_path_summary"])
    safety = cast(Mapping[str, object], evidence["safety"])

    lines = [
        "# Phase 5E A100 Real-Training Preflight",
        "",
        f"Status: {status}",
        "",
        "Boundary: setup/preflight only; real training was not launched.",
        "",
        "## Remote readiness",
        "",
        f"- CUDA available: {str(cuda['available']).lower()}",
        f"- CUDA device count: {cuda.get('device_count')}",
        f"- GPU model summary: {cuda.get('gpu_model_summary')}",
        "- Safe idle GPU candidates: "
        + json.dumps(cuda.get("safe_idle_gpu_candidates"), sort_keys=True),
        "- Runtime modules: "
        + json.dumps(runtime.get("module_available"), sort_keys=True),
        f"- Local model path provided: {str(model_summary['provided']).lower()}",
        f"- Local model path exists: {str(model_summary['exists']).lower()}",
        "",
        "## Blocked reasons",
        "",
    ]
    if blockers:
        for reason in blockers:
            lines.append(f"- {reason['code']}: {reason['message']}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- training launched: {str(safety['training_launched']).lower()}",
            "- model download executed: "
            f"{str(safety['model_download_executed']).lower()}",
            f"- final test used: {str(safety['final_test_used']).lower()}",
            "- adapter checkpoint created: "
            f"{str(safety['adapter_checkpoint_created']).lower()}",
            "- benchmark improvement claim: "
            f"{str(safety['benchmark_improvement_claim']).lower()}",
            "",
        ]
    )
    return "\n".join(lines)


def render_phase_5f_run_card(evidence: Mapping[str, object]) -> str:
    """Render a compact public-safe Phase 5F runtime-gate run card."""

    status = str(evidence["status"])
    blockers = cast(Sequence[Mapping[str, object]], evidence["blocked_reasons"])
    runtime_gates = cast(Mapping[str, object], evidence["runtime_gates"])
    safety = cast(Mapping[str, object], evidence["safety"])

    lines = [
        "# Phase 5F A100 Runtime Gate Materialization",
        "",
        f"Status: {status}",
        "",
        "Boundary: runtime-gate materialization only; real training was not launched.",
        "",
        "## Runtime gates",
        "",
    ]
    for gate_name in (
        "allowed_root_placement",
        "dependency_importability",
        "cuda_and_gpu",
        "local_model_path",
    ):
        gate = cast(Mapping[str, object], runtime_gates[gate_name])
        lines.append(f"- {gate_name}: ready={str(gate['ready']).lower()}")

    lines.extend(["", "## Blocked reasons", ""])
    if blockers:
        for reason in blockers:
            lines.append(f"- {reason['code']}: {reason['message']}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- training launched: {str(safety['training_launched']).lower()}",
            "- model download executed: "
            f"{str(safety['model_download_executed']).lower()}",
            "- network model resolution: "
            f"{str(safety['network_used_for_model_resolution']).lower()}",
            f"- final test used: {str(safety['final_test_used']).lower()}",
            "- adapter checkpoint created: "
            f"{str(safety['adapter_checkpoint_created']).lower()}",
            "- benchmark improvement claim: "
            f"{str(safety['benchmark_improvement_claim']).lower()}",
            "",
        ]
    )
    return "\n".join(lines)


def _safety_summary(*, status: str) -> dict[str, object]:
    return {
        "schema": "phase_5e_a100_preflight_safety/v1",
        "status": status,
        "training_launched": False,
        "model_download_executed": False,
        "network_used_for_model_resolution": False,
        "final_test_used": False,
        "adapter_checkpoint_created": False,
        "adapter_checkpoint_committed": False,
        "model_weights_committed": False,
        "training_cache_committed": False,
        "private_local_model_path_committed": False,
        "host_ip_committed": False,
        "ssh_details_committed": False,
        "process_ids_committed": False,
        "benchmark_improvement_claim": False,
        "real_training_success_claim": False,
    }


def _safe_idle_gpu_candidates(gpus: Sequence[Mapping[str, object]]) -> list[int]:
    candidates: list[int] = []
    for gpu in gpus:
        index = _optional_int(gpu.get("index"))
        used = _optional_int(gpu.get("memory_used_mib"))
        util = _optional_int(gpu.get("utilization_gpu_percent"))
        if index is None or used is None or util is None:
            continue
        if used <= IDLE_GPU_MAX_MEMORY_MIB and util <= IDLE_GPU_MAX_UTILIZATION_PERCENT:
            candidates.append(index)
    return candidates


def _busy_gpu_count(gpus: Sequence[Mapping[str, object]]) -> int:
    return len(gpus) - len(_safe_idle_gpu_candidates(gpus))


def _gpu_model_summary(gpus: Sequence[Mapping[str, object]]) -> str:
    names: dict[str, int] = {}
    for gpu in gpus:
        name = str(gpu.get("name", "unknown"))
        names[name] = names.get(name, 0) + 1
    if not names:
        return "unknown"
    return ", ".join(f"{count}x {name}" for name, count in sorted(names.items()))


def _model_path_location(model_path: Mapping[str, object]) -> str:
    if model_path.get("provided") is not True:
        return "not_provided"
    path = str(model_path.get("path", ""))
    if _is_under_allowed_root(path):
        return "under_allowed_root"
    if path:
        return "outside_allowed_root_or_private"
    return "redacted"


def _overall_status(blockers: Sequence[Mapping[str, object]]) -> str:
    if not blockers:
        return "preflight_ready"
    codes = {str(reason["code"]) for reason in blockers}
    if codes <= {"needs_user_model_path"}:
        return "needs_user_input"
    return "blocked"


def _phase_5f_status(blockers: Sequence[Mapping[str, object]]) -> str:
    if not blockers:
        return "runtime_ready"
    codes = {str(reason["code"]) for reason in blockers}
    if codes <= {"needs_user_model_path"}:
        return "needs_user_input"
    return "blocked"


def _model_path_a100_readable(model_path: Mapping[str, object]) -> bool:
    if model_path.get("provided") is not True or model_path.get("exists") is not True:
        return False
    return model_path.get("a100_readable") is True


def _is_under_allowed_root(path: str) -> bool:
    try:
        parsed = PurePosixPath(path)
        parsed.relative_to(ALLOWED_REMOTE_ROOT)
    except ValueError:
        return False
    return True


def _add_blocker(blockers: list[dict[str, object]], code: str, message: str) -> None:
    blockers.append({"code": code, "message": message})


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, str) else ()


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_public_str(value: object) -> str | None:
    return value if isinstance(value, str) and _is_public_safe(value) else None


def _is_public_safe(value: str) -> bool:
    lowered = value.lower()
    blocked_fragments = (
        "ssh-rsa",
        "private key",
        "token" + "=",
        "password" + "=",
    )
    return not IPV4_RE.search(value) and not any(
        fragment in lowered for fragment in blocked_fragments
    )


def _write_json(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("5e", "5f"), default="5e")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--environment-check", required=True, type=Path)
    parser.add_argument("--safety-check", required=True, type=Path)
    parser.add_argument("--run-card", required=True, type=Path)
    parser.add_argument("--timestamp-utc")
    args = parser.parse_args(argv)

    observation = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(observation, Mapping):
        raise SystemExit("input observation must be a JSON object")
    write_outputs = (
        write_phase_5f_outputs if args.phase == "5f" else write_phase_5e_outputs
    )
    evidence = write_outputs(
        observation,
        environment_check_path=args.environment_check,
        safety_check_path=args.safety_check,
        run_card_path=args.run_card,
        report_timestamp_utc=args.timestamp_utc,
    )
    print(f"phase {args.phase} preflight status: {evidence['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
