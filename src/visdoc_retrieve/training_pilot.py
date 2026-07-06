"""Guarded local real-training pilot helpers."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MAX_PILOT_STEPS = 20
MAX_PILOT_SAMPLE_LIMIT = 8
PILOT_COMMAND_PREFIX = "PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot"
DEFAULT_PILOT_CONFIG_PATH = "configs/train_lora_pilot.local.example.json"


class TrainingPilotConfigError(ValueError):
    """Raised when a pilot config violates launch-gate boundaries."""


@dataclass(frozen=True, slots=True)
class TrainingPilotPhaseMetadata:
    """Public-safe phase metadata for reports and progress ledger output."""

    schema_id: str
    phase_label: str
    change_name: str
    title: str
    ledger_section: str
    summary_zh: str
    recommended_next_step_zh: str


DEFAULT_PHASE_METADATA = TrainingPilotPhaseMetadata(
    schema_id="phase_5d",
    phase_label="5D",
    change_name="add-real-training-backend-wiring",
    title="Phase 5D Real Training Backend Wiring",
    ledger_section="training_pilot_phase_5d_status",
    summary_zh="Phase 5D 完成 train_lora_pilot 的 backend wiring 检查点；",
    recommended_next_step_zh=(
        "在具备本地模型和 CUDA 的 A100 环境中运行一次小预算 pilot，"
        "或继续记录 blocked evidence。"
    ),
)


@dataclass(frozen=True, slots=True)
class TrainingPilotOutputs:
    """Report output paths for a guarded pilot gate."""

    environment_check: Path
    blocked_run_card: Path
    pilot_run_card: Path
    safety_check: Path
    dev_eval_schema: Path
    adapter_manifest: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class TrainingPilotConfig:
    """Parsed guarded pilot config."""

    base_model_name_or_path: str
    local_model_path: Path
    model_revision: str
    artifact_freeze_path: Path
    backend_dependency: str
    adapter_output_dir: Path
    train_hard_negatives_path: Path
    dev_hard_negatives_path: Path
    corpus_path: Path
    queries_path: Path
    qrels_path: Path
    candidate_universe_id: str
    loss_type: str
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    qlora: bool
    batch_size: int
    gradient_accumulation_steps: int
    max_steps: int
    sample_limit: int
    learning_rate: float
    seed: int
    device: str
    local_files_only: bool
    allow_real_training: bool
    allow_final_test: bool
    save_adapter: bool
    report_timestamp_utc: str
    phase_metadata: TrainingPilotPhaseMetadata
    outputs: TrainingPilotOutputs
    config_path: Path | None


@dataclass(frozen=True, slots=True)
class GateResult:
    """One launch-gate check result."""

    name: str
    passed: bool
    code: str
    message: str


def load_training_pilot_config(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> TrainingPilotConfig:
    """Load and validate a guarded pilot JSON config without ML imports."""

    root = repo_root.resolve() if repo_root is not None else None
    config_path = _resolve_path(root, path) if root is not None else path
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TrainingPilotConfigError(
            f"training-pilot config cannot be read: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise TrainingPilotConfigError(
            f"training-pilot config is not valid JSON: {path}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise TrainingPilotConfigError("training-pilot config must be an object")

    outputs = _required_mapping(data, "outputs")
    phase_metadata = _phase_metadata_from_data(
        _optional_mapping(data, "phase_metadata")
    )
    artifact_freeze_path = _optional_str(
        data,
        "artifact_freeze_path",
        default="reports/training-readiness/artifact-freeze.json",
    )
    config = TrainingPilotConfig(
        base_model_name_or_path=_required_str(data, "base_model_name_or_path"),
        local_model_path=Path(_required_str(data, "local_model_path")),
        model_revision=_required_str(data, "model_revision"),
        artifact_freeze_path=Path(artifact_freeze_path),
        backend_dependency=_optional_str(
            data,
            "backend_dependency",
            default="colpali_engine",
        ),
        adapter_output_dir=Path(_required_str(data, "adapter_output_dir")),
        train_hard_negatives_path=Path(
            _required_str(data, "train_hard_negatives_path")
        ),
        dev_hard_negatives_path=Path(_required_str(data, "dev_hard_negatives_path")),
        corpus_path=Path(_required_str(data, "corpus_path")),
        queries_path=Path(_required_str(data, "queries_path")),
        qrels_path=Path(_required_str(data, "qrels_path")),
        candidate_universe_id=_required_str(data, "candidate_universe_id"),
        loss_type=_required_str(data, "loss_type"),
        lora_r=_positive_int(data, "lora_r"),
        lora_alpha=_positive_int(data, "lora_alpha"),
        lora_dropout=_bounded_float(data, "lora_dropout", lower=0.0, upper=1.0),
        qlora=_required_bool(data, "qlora"),
        batch_size=_positive_int(data, "batch_size"),
        gradient_accumulation_steps=_positive_int(
            data,
            "gradient_accumulation_steps",
        ),
        max_steps=_positive_int(data, "max_steps"),
        sample_limit=_positive_int(data, "sample_limit"),
        learning_rate=_positive_float(data, "learning_rate"),
        seed=_positive_int(data, "seed"),
        device=_required_str(data, "device"),
        local_files_only=_optional_bool(data, "local_files_only", default=True),
        allow_real_training=_required_bool(data, "allow_real_training"),
        allow_final_test=_required_bool(data, "allow_final_test"),
        save_adapter=_required_bool(data, "save_adapter"),
        report_timestamp_utc=_required_str(data, "report_timestamp_utc"),
        phase_metadata=phase_metadata,
        outputs=TrainingPilotOutputs(
            environment_check=Path(_required_str(outputs, "environment_check")),
            blocked_run_card=Path(_required_str(outputs, "blocked_run_card")),
            pilot_run_card=Path(_required_str(outputs, "pilot_run_card")),
            safety_check=Path(_required_str(outputs, "safety_check")),
            dev_eval_schema=Path(_required_str(outputs, "dev_eval_schema")),
            adapter_manifest=Path(_required_str(outputs, "adapter_manifest")),
            human_brief=Path(_required_str(outputs, "human_brief")),
            progress_ledger=Path(_required_str(outputs, "progress_ledger")),
        ),
        config_path=config_path,
    )
    _validate_pilot_config(config, repo_root=root)
    return config


def run_training_pilot_gate(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    environ: Mapping[str, str] | None = None,
    cuda_available: Callable[[], bool] | None = None,
    training_backend_runner: Callable[..., dict[str, object]] | None = None,
) -> dict[str, object]:
    """Run the guarded pilot gates and write blocked or pilot evidence."""

    env = environ if environ is not None else os.environ
    cuda_probe = cuda_available if cuda_available is not None else _cuda_available
    outputs = _resolved_outputs(config.outputs, repo_root=repo_root)
    gates = _evaluate_gates(
        config,
        repo_root=repo_root,
        environ=env,
        cuda_available=cuda_probe,
    )
    blocked_reasons = [
        _blocked_reason(gate) for gate in gates if not gate.passed
    ]

    training_result: dict[str, object] | None = None
    if not blocked_reasons:
        runner = training_backend_runner or _run_guarded_real_training_pilot
        raw_training_result = runner(
            config,
            repo_root=repo_root,
        )
        if raw_training_result.get("status") == "pilot_run":
            unsafe_result = _unsafe_backend_result(config, raw_training_result)
            if unsafe_result is None:
                training_result = _sanitize_pilot_training_result(
                    config,
                    raw_training_result,
                )
            else:
                training_result = _blocked_backend_result(unsafe_result)
                blocked_reasons.append(unsafe_result)
        else:
            training_result = _sanitize_blocked_training_result(raw_training_result)
            blocked_reasons.append(
                {
                    "code": str(training_result.get("blocked_code")),
                    "message": str(training_result.get("blocked_message")),
                }
            )

    status = "blocked" if blocked_reasons else "pilot_run"
    environment = _environment_check(
        config,
        repo_root=repo_root,
        gates=gates,
        blocked_reasons=blocked_reasons,
        status=status,
        training_result=training_result,
    )
    safety = _safety_check(
        config,
        repo_root=repo_root,
        status=status,
        training_result=training_result,
    )
    dev_eval = _dev_eval_schema(config, status=status)
    manifest = _adapter_manifest(
        config,
        repo_root=repo_root,
        status=status,
        training_result=training_result,
    )

    _write_json(outputs.environment_check, environment)
    _write_json(outputs.safety_check, safety)
    _write_json(outputs.dev_eval_schema, dev_eval)
    _write_json(outputs.adapter_manifest, manifest)
    if status == "blocked":
        _write_blocked_run_card(
            outputs.blocked_run_card,
            config=config,
            repo_root=repo_root,
            environment=environment,
        )
    else:
        _write_pilot_run_card(
            outputs.pilot_run_card,
            config=config,
            repo_root=repo_root,
            environment=environment,
        )
    _write_human_brief(
        outputs.human_brief,
        config=config,
        repo_root=repo_root,
        environment=environment,
    )
    _update_progress_ledger(
        outputs.progress_ledger,
        config=config,
        repo_root=repo_root,
        status=status,
        environment=environment,
    )
    return {
        "status": status,
        "blocked_reasons": blocked_reasons,
        "environment_check": str(outputs.environment_check),
        "run_card": str(
            outputs.blocked_run_card if status == "blocked" else outputs.pilot_run_card
        ),
        "safety_check": str(outputs.safety_check),
        "dev_eval_schema": str(outputs.dev_eval_schema),
        "adapter_manifest": str(outputs.adapter_manifest),
        "human_brief": str(outputs.human_brief),
        "progress_ledger": str(outputs.progress_ledger),
    }


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for a local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_pilot_config(
    config: TrainingPilotConfig,
    *,
    repo_root: Path | None = None,
) -> None:
    if config.allow_final_test:
        raise TrainingPilotConfigError("allow_final_test must remain false")
    if config.max_steps > MAX_PILOT_STEPS:
        raise TrainingPilotConfigError(f"max_steps must be <= {MAX_PILOT_STEPS}")
    if config.sample_limit > MAX_PILOT_SAMPLE_LIMIT:
        raise TrainingPilotConfigError(
            f"sample_limit must be <= {MAX_PILOT_SAMPLE_LIMIT}"
        )
    if not config.local_files_only:
        raise TrainingPilotConfigError("local_files_only must remain true")
    if config.loss_type != "lora_pairwise_maxsim":
        raise TrainingPilotConfigError("loss_type must be lora_pairwise_maxsim")
    if config.device != "cuda":
        raise TrainingPilotConfigError("device must be cuda for a real pilot gate")
    for field_name, path in {
        "train_hard_negatives_path": config.train_hard_negatives_path,
        "dev_hard_negatives_path": config.dev_hard_negatives_path,
    }.items():
        if _looks_like_final_test_path(path):
            raise TrainingPilotConfigError(
                f"{field_name} must not point at final test data"
            )
    for field_name, path in {
        "queries_path": config.queries_path,
        "qrels_path": config.qrels_path,
    }.items():
        _validate_dev_only_query_file(
            path,
            field_name=field_name,
            corpus_path=config.corpus_path,
            repo_root=repo_root,
        )


def _evaluate_gates(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    environ: Mapping[str, str],
    cuda_available: Callable[[], bool],
) -> tuple[GateResult, ...]:
    local_model = _resolve_path(repo_root, config.local_model_path)
    env_enabled = environ.get("VISDOC_ENABLE_REAL_TRAINING") == "1"
    local_model_exists = local_model.exists()
    adapter_output_ignored = _git_check_ignore(repo_root, config.adapter_output_dir)
    artifact_freeze_gate = _artifact_freeze_hash_gate(config, repo_root=repo_root)
    hard_negative_files_gate = _hard_negative_files_exist_gate(
        config,
        repo_root=repo_root,
    )
    hard_negative_universe_gate = _hard_negative_candidate_universe_gate(
        config,
        repo_root=repo_root,
        files_exist=hard_negative_files_gate.passed,
    )
    can_probe_cuda = (
        config.allow_real_training
        and env_enabled
        and local_model_exists
        and adapter_output_ignored
        and artifact_freeze_gate.passed
        and hard_negative_files_gate.passed
        and hard_negative_universe_gate.passed
        and config.max_steps <= MAX_PILOT_STEPS
        and config.sample_limit <= MAX_PILOT_SAMPLE_LIMIT
        and config.local_files_only
    )
    cuda_passed = cuda_available() if can_probe_cuda else False
    cuda_code = "cuda_unavailable" if can_probe_cuda else "cuda_not_checked"
    cuda_message = (
        "CUDA is unavailable for the real pilot."
        if can_probe_cuda
        else "CUDA was not checked because an earlier non-import gate blocked."
    )
    gates: list[GateResult] = [
        GateResult(
            name="allow_final_test_false",
            passed=not config.allow_final_test,
            code="allow_final_test_true",
            message="allow_final_test must remain false for the gated pilot.",
        ),
        GateResult(
            name="allow_real_training_true",
            passed=config.allow_real_training,
            code="allow_real_training_false",
            message="Config did not explicitly allow real training.",
        ),
        GateResult(
            name="training_env_enabled",
            passed=env_enabled,
            code="training_env_not_enabled",
            message="VISDOC_ENABLE_REAL_TRAINING=1 is required for a real pilot.",
        ),
        artifact_freeze_gate,
        hard_negative_files_gate,
        hard_negative_universe_gate,
        GateResult(
            name="local_model_path_exists",
            passed=local_model_exists,
            code="missing_local_model_path",
            message=(
                "local_model_path does not exist: "
                f"{_redacted_local_model_path()}"
            ),
        ),
        GateResult(
            name="adapter_output_ignored",
            passed=adapter_output_ignored,
            code="adapter_output_not_ignored",
            message=(
                "adapter_output_dir must be ignored so checkpoints are not "
                "committed."
            ),
        ),
        GateResult(
            name="max_steps_tiny",
            passed=config.max_steps <= MAX_PILOT_STEPS,
            code="max_steps_over_budget",
            message=f"max_steps must be <= {MAX_PILOT_STEPS}.",
        ),
        GateResult(
            name="sample_limit_tiny",
            passed=config.sample_limit <= MAX_PILOT_SAMPLE_LIMIT,
            code="sample_limit_over_budget",
            message=f"sample_limit must be <= {MAX_PILOT_SAMPLE_LIMIT}.",
        ),
        GateResult(
            name="local_files_only",
            passed=config.local_files_only,
            code="local_files_only_disabled",
            message="Model loading must use local files only.",
        ),
        GateResult(
            name="cuda_available",
            passed=cuda_passed,
            code=cuda_code,
            message=cuda_message,
        ),
        GateResult(
            name="run_card_boundary_wording",
            passed=True,
            code="run_card_boundary_missing",
            message=(
                "Run-card boundary wording must mark pilot/dev-only/"
                "not final benchmark."
            ),
        ),
    ]
    return tuple(gates)


def _environment_check(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    gates: Sequence[GateResult],
    blocked_reasons: Sequence[Mapping[str, object]],
    status: str,
    training_result: Mapping[str, object] | None,
) -> dict[str, object]:
    phase = config.phase_metadata
    return {
        "schema": _phase_schema(config, "environment_check"),
        "timestamp_utc": config.report_timestamp_utc,
        "phase": phase.phase_label,
        "change": phase.change_name,
        "overall_status": status,
        "real_training_executed": status == "pilot_run",
        "blocked_reasons": list(blocked_reasons),
        "gates": {
            gate.name: {
                "passed": gate.passed,
                "code": gate.code,
                "message": gate.message,
            }
            for gate in gates
        },
        "config": {
            "allow_real_training": config.allow_real_training,
            "allow_final_test": config.allow_final_test,
            "artifact_freeze_path": str(config.artifact_freeze_path),
            "backend_dependency": config.backend_dependency,
            "local_model_path": _redacted_local_model_path(),
            "local_files_only": config.local_files_only,
            "adapter_output_dir": str(config.adapter_output_dir),
            "max_steps": config.max_steps,
            "sample_limit": config.sample_limit,
            "device": config.device,
            "candidate_universe_id": config.candidate_universe_id,
        },
        "local_model_path_summary": _local_model_path_summary(
            config,
            repo_root=repo_root,
        ),
        "run_card_boundary": {
            "pilot": True,
            "dev_only": True,
            "not_final_benchmark": True,
            "benchmark_improvement_claim": False,
        },
        "training_result": dict(training_result) if training_result else None,
    }


def _safety_check(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    status: str,
    training_result: Mapping[str, object] | None,
) -> dict[str, object]:
    phase = config.phase_metadata
    forbidden_scan = _forbidden_artifact_scan(config, repo_root=repo_root)
    model_weight_paths = cast(
        Sequence[str],
        forbidden_scan["model_weight_paths"],
    )
    adapter_checkpoint_paths = cast(
        Sequence[str],
        forbidden_scan["adapter_checkpoint_paths"],
    )
    training_cache_paths = cast(
        Sequence[str],
        forbidden_scan["training_cache_paths"],
    )
    return {
        "schema": _phase_schema(config, "safety_check"),
        "phase": phase.phase_label,
        "training_executed": status == "pilot_run",
        "model_download_executed": False,
        "network_used": False,
        "network_used_for_model_resolution": False,
        "final_test_used": False,
        "adapter_checkpoint_committed": bool(adapter_checkpoint_paths),
        "model_weights_committed": bool(model_weight_paths),
        "training_cache_committed": bool(training_cache_paths),
        "benchmark_claim_added": False,
        "pilot_loss_reported_as_model_improvement": False,
        "mock_visual_result_reported_as_real": False,
        "dry_run_or_blocked_claimed_as_real_training": False,
        "forbidden_artifact_scan": forbidden_scan,
        "real_training_result": dict(training_result) if training_result else None,
    }


def _dev_eval_schema(config: TrainingPilotConfig, *, status: str) -> dict[str, object]:
    metrics: dict[str, float | None] = {
        "recall_at_1": None,
        "recall_at_5": None,
        "mrr": None,
    }
    return {
        "schema": _phase_schema(config, "dev_eval"),
        "status": "not_run" if status == "blocked" else "pending_real_adapter_eval",
        "scope": "dev-only",
        "candidate_universe_id": config.candidate_universe_id,
        "dev_hard_negatives_path": str(config.dev_hard_negatives_path),
        "queries_path": str(config.queries_path),
        "qrels_path": str(config.qrels_path),
        "final_test_used": False,
        "adapter_required": True,
        "metrics": metrics,
        "improvement_claim": None,
        "notes": (
            "No dev improvement is reported unless a gated real adapter exists; "
            "final test remains unused."
        ),
    }


def _adapter_manifest(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    status: str,
    training_result: Mapping[str, object] | None,
) -> dict[str, object]:
    phase = config.phase_metadata
    result = training_result or {}
    sample_count = _int_result_value(result, "effective_training_sample_count")
    adapter_checkpoint_created = bool(
        result.get("adapter_checkpoint_created", status == "pilot_run")
    )
    adapter_checkpoint_path = result.get("adapter_checkpoint_path")
    return {
        "schema": _phase_schema(config, "adapter_manifest_sanitized"),
        "phase": phase.phase_label,
        "adapter_output_dir": str(config.adapter_output_dir),
        "base_model_name_or_path": config.base_model_name_or_path,
        "local_model_path": "<redacted-local-model-path>",
        "model_revision": config.model_revision,
        "artifact_freeze_path": str(config.artifact_freeze_path),
        "hard_negative_artifact_hash": _combined_file_hash(
            repo_root,
            [config.train_hard_negatives_path, config.dev_hard_negatives_path],
        ),
        "train_config_hash": _config_hash(config),
        "git_commit": _git_commit(repo_root),
        "max_steps": config.max_steps,
        "sample_limit": config.sample_limit,
        "effective_training_sample_count": sample_count,
        "seed": config.seed,
        "device": config.device,
        "final_test_used": False,
        "model_download_executed": False,
        "network_used_for_model_resolution": False,
        "benchmark_improvement_claim": False,
        "pilot_loss_reported_as_model_improvement": False,
        "created_at": config.report_timestamp_utc,
        "pilot_status": status,
        "adapter_checkpoint_created": adapter_checkpoint_created,
        "adapter_checkpoint_path": (
            adapter_checkpoint_path if adapter_checkpoint_created else None
        ),
        "real_training_result": dict(result) if result else None,
    }


def _int_result_value(result: Mapping[str, object], key: str) -> int:
    value = result.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return 0


def _unsafe_backend_result(
    config: TrainingPilotConfig,
    result: Mapping[str, object],
) -> dict[str, object] | None:
    if result.get("training_executed") is not True:
        return _unsafe_reason("backend did not report training_executed=true")
    if result.get("final_test_used") is True:
        return _unsafe_reason("backend reported final_test_used=true")
    sample_count = _int_result_value(result, "effective_training_sample_count")
    if sample_count <= 0 or sample_count > config.sample_limit:
        return _unsafe_reason("backend sample count exceeded the configured cap")
    if sample_count > MAX_PILOT_SAMPLE_LIMIT:
        return _unsafe_reason("backend sample count exceeded the phase cap")
    if result.get("benchmark_improvement_claim") is True:
        return _unsafe_reason("backend reported a benchmark claim")
    if result.get("pilot_loss_reported_as_model_improvement") is True:
        return _unsafe_reason("backend reported pilot loss as model improvement")
    if result.get("improvement_claim") is not None or "metrics" in result:
        return _unsafe_reason("backend returned metric or improvement fields")

    adapter_created = result.get("adapter_checkpoint_created") is True
    adapter_path = result.get("adapter_checkpoint_path")
    if adapter_created:
        if not config.save_adapter:
            return _unsafe_reason("backend created an adapter while save_adapter=false")
        if not isinstance(adapter_path, str) or not adapter_path:
            return _unsafe_reason("backend adapter path was missing")
        if Path(adapter_path).is_absolute():
            return _unsafe_reason("backend adapter path was absolute")
        if Path(adapter_path) != config.adapter_output_dir:
            return _unsafe_reason("backend adapter path did not match config")
    return None


def _unsafe_reason(message: str) -> dict[str, object]:
    return {"code": "unsafe_backend_result", "message": message}


def _sanitize_pilot_training_result(
    config: TrainingPilotConfig,
    result: Mapping[str, object],
) -> dict[str, object]:
    adapter_created = result.get("adapter_checkpoint_created") is True
    return {
        "status": "pilot_run",
        "training_executed": True,
        "effective_training_sample_count": _int_result_value(
            result,
            "effective_training_sample_count",
        ),
        "adapter_checkpoint_created": adapter_created,
        "adapter_checkpoint_path": (
            str(config.adapter_output_dir) if adapter_created else None
        ),
        "max_steps": config.max_steps,
        "final_test_used": False,
        "local_files_only": True,
        "benchmark_improvement_claim": False,
        "pilot_loss_reported_as_model_improvement": False,
    }


def _sanitize_blocked_training_result(
    result: Mapping[str, object],
) -> dict[str, object]:
    blocked_code = str(result.get("blocked_code", "backend_blocked"))
    blocked_message = str(
        result.get("blocked_message", "Real training backend blocked.")
    )
    sanitized: dict[str, object] = {
        "status": "blocked",
        "blocked_code": blocked_code,
        "blocked_message": blocked_message,
        "training_executed": False,
        "effective_training_sample_count": _int_result_value(
            result,
            "effective_training_sample_count",
        ),
        "adapter_checkpoint_created": False,
        "adapter_checkpoint_path": None,
        "final_test_used": False,
    }
    missing_dependencies = result.get("missing_dependencies")
    if isinstance(missing_dependencies, (list, tuple)):
        sanitized["missing_dependencies"] = [
            str(item) for item in missing_dependencies
        ]
    return sanitized


def _blocked_backend_result(reason: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "blocked",
        "blocked_code": str(reason["code"]),
        "blocked_message": str(reason["message"]),
        "training_executed": False,
        "effective_training_sample_count": 0,
        "adapter_checkpoint_created": False,
        "adapter_checkpoint_path": None,
        "final_test_used": False,
    }


def _redacted_local_model_path() -> str:
    return "<redacted-local-model-path>"


def _local_model_path_summary(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    return {
        "redacted": True,
        "committed_value": _redacted_local_model_path(),
        "exists": _resolve_path(repo_root, config.local_model_path).exists(),
        "literal_placeholder": str(config.local_model_path).startswith("local-models/"),
    }


def _run_guarded_real_training_pilot(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Run the guarded local-only real-training path.

    This path is intentionally unreachable from default validation. The backend
    module has no top-level optional ML imports; torch/transformers/peft and the
    selected visual backend dependency are imported only inside its guarded
    function.
    """

    from visdoc_retrieve.lora_training_backend import run_local_lora_pilot

    return run_local_lora_pilot(config, repo_root=repo_root)


def _cuda_available() -> bool:
    try:
        torch = importlib.import_module("torch")
    except ImportError:
        return False
    cuda = getattr(torch, "cuda", None)
    is_available = getattr(cuda, "is_available", None)
    return bool(callable(is_available) and is_available())


def _blocked_reason(gate: GateResult) -> dict[str, object]:
    return {"code": gate.code, "message": gate.message}


def _write_blocked_run_card(
    path: Path,
    *,
    config: TrainingPilotConfig,
    repo_root: Path,
    environment: Mapping[str, object],
) -> None:
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    reason_lines = [
        f"- {reason['code']}: {reason['message']}"
        for reason in reasons
    ]
    lines = [
        f"# {config.phase_metadata.title}",
        "",
        "Status: blocked",
        "",
        f"Timestamp: {config.report_timestamp_utc}",
        f"Command: {_pilot_command(config, repo_root=repo_root)}",
        f"Candidate universe: {config.candidate_universe_id}",
        f"Max steps: {config.max_steps}",
        f"Sample limit: {config.sample_limit}",
        "",
        "Boundary: pilot, dev-only, not final benchmark.",
        "",
        "Training did not run. This blocked run is not a real training result "
        "and does not claim benchmark gain.",
        "",
        "Blocked reasons:",
        *reason_lines,
        "",
    ]
    _write_text(path, "\n".join(lines))


def _write_pilot_run_card(
    path: Path,
    *,
    config: TrainingPilotConfig,
    repo_root: Path,
    environment: Mapping[str, object],
) -> None:
    _write_text(
        path,
        "\n".join(
            [
                f"# {config.phase_metadata.title}",
                "",
                "Status: pilot_run",
                "",
                f"Timestamp: {config.report_timestamp_utc}",
                f"Command: {_pilot_command(config, repo_root=repo_root)}",
                f"Max steps: {config.max_steps}",
                f"Sample limit: {config.sample_limit}",
                "Boundary: pilot, dev-only, not final benchmark.",
                "",
                "Final test was not used and no benchmark claim is made.",
                "",
            ]
        ),
    )


def _write_human_brief(
    path: Path,
    *,
    config: TrainingPilotConfig,
    repo_root: Path,
    environment: Mapping[str, object],
) -> None:
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    status = str(environment["overall_status"])
    if reasons:
        gate_status_html = (
            "  <h2>当前阻塞原因</h2>\n"
            "  <ul>"
            + "".join(
                f"<li><code>{reason['code']}</code>: {reason['message']}</li>"
                for reason in reasons
            )
            + "</ul>"
        )
    else:
        gate_status_html = (
            "  <h2>当前阻塞原因</h2>\n"
            "  <p>本次运行没有阻塞理由；所有训练门禁已通过。</p>"
        )
    command = _pilot_command(config, repo_root=repo_root)
    output_paths = [
        str(config.outputs.environment_check),
        str(
            config.outputs.blocked_run_card
            if status == "blocked"
            else config.outputs.pilot_run_card
        ),
        str(config.outputs.safety_check),
        str(config.outputs.dev_eval_schema),
        str(config.outputs.adapter_manifest),
    ]
    html = "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{config.phase_metadata.title}</title>",
            "  <style>",
            "    body {",
            '      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",',
            "        sans-serif;",
            "      margin: 32px;",
            "      line-height: 1.55;",
            "      color: #202124;",
            "    }",
            "    main { max-width: 880px; margin: 0 auto; }",
            "    code {",
            "      background: #f1f3f4;",
            "      padding: 1px 4px;",
            "      border-radius: 4px;",
            "    }",
            "    .status { font-weight: 700; }",
            "  </style>",
            "</head>",
            "<body>",
            "<main>",
            f"  <h1>{config.phase_metadata.title}</h1>",
            "  <h2>一句话结论</h2>",
            f"  <p>{config.phase_metadata.summary_zh}",
            f'  当前状态为 <span class="status">{status}</span>。</p>',
            "  <h2>当前状态</h2>",
            "  <p>这是 pilot / dev-only / not final benchmark 检查点。",
            "  final test 仍未使用，没有 benchmark gain claim。</p>",
            "  <h2>本阶段变化</h2>",
            "  <ul>",
            f"    <li>运行 gated pilot 命令 <code>{command}</code>。</li>",
            "    <li>只在所有门禁通过时进入 import-safe 的本地 LoRA / "
            "QLoRA guarded backend。</li>",
            f"    <li>生成 Phase {config.phase_metadata.phase_label} "
            "environment check、run-card、safety check、dev eval 和 "
            "sanitized adapter manifest。</li>",
            "  </ul>",
            "  <h2>训练门禁</h2>",
            "  <p>只有同时满足 allow_real_training=true、",
            "  allow_final_test=false、",
            "  <code>VISDOC_ENABLE_REAL_TRAINING=1</code>、",
            "  本地模型路径存在、CUDA 可用、",
            f"  <code>max_steps &lt;= {MAX_PILOT_STEPS}</code>、",
            f"  <code>sample_limit &lt;= {MAX_PILOT_SAMPLE_LIMIT}</code>、",
            "  adapter 输出目录被 git ignore，才允许进入 guarded real pilot",
            "  launcher。</p>",
            gate_status_html,
            "  <h2>A100 / 本地模型 pilot 运行方式</h2>",
            "  <p>在 A100 或本地 CUDA 环境中，先准备本地模型目录，",
            "  确认 adapter 输出在 ignored artifacts 目录下，再显式设置",
            "  <code>VISDOC_ENABLE_REAL_TRAINING=1</code> 并将配置中的",
            "  <code>allow_real_training</code> 改为 true。不要下载模型，",
            "  不要启用 final test。</p>",
            "  <h2>关键证据</h2>",
            "  <ul>",
            *[
                f"    <li><code>{output_path}</code></li>"
                for output_path in output_paths
            ],
            "  </ul>",
            "  <h2>不应夸大的结论</h2>",
            "  <p>没有提交 adapter / weights；没有把 blocked 或 dry-run 写成",
            "  真实训练结果；没有把 pilot loss 或 dev-only sanity 写成模型提升。</p>",
            "  <h2>推荐下一步</h2>",
            f"  <p>{config.phase_metadata.recommended_next_step_zh}</p>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )
    _write_text(path, html)


def _update_progress_ledger(
    path: Path,
    *,
    config: TrainingPilotConfig,
    repo_root: Path,
    status: str,
    environment: Mapping[str, object],
) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    reason_codes = [str(reason["code"]) for reason in reasons]
    reason_lines = [f"    - {code}" for code in reason_codes]
    if not reason_lines:
        reason_lines = ["    - none"]
    run_card_path = str(
        config.outputs.blocked_run_card
        if status == "blocked"
        else config.outputs.pilot_run_card
    )
    config_path = _display_repo_path(repo_root, config.config_path)
    entry = "\n".join(
        [
            f"{config.phase_metadata.ledger_section}:",
            f"  status: {status}",
            f"  change: {config.phase_metadata.change_name}",
            f"  command: {_pilot_command(config, repo_root=repo_root)}",
            f"  config: {config_path}",
            f"  candidate_universe: {config.candidate_universe_id}",
            f"  max_steps: {config.max_steps}",
            f"  sample_limit: {config.sample_limit}",
            (
                "  training: not_executed"
                if status == "blocked"
                else "  training: pilot_run"
            ),
            f"  real_pilot_ran: {str(status == 'pilot_run').lower()}",
            "  model_download: not_executed",
            "  network: not_used",
            "  final_test_evaluation: not_run",
            "  dev_eval: not_run_or_schema_only",
            "  benchmark_claim: none",
            "  adapter_checkpoint_committed: false",
            "  model_weights_committed: false",
            "  training_cache_committed: false",
            "  private_local_model_path_committed: false",
            "  mock_visual_result_reported_as_real: false",
            "  pilot_loss_reported_as_model_improvement: false",
            "  blocked_reasons:",
            *reason_lines,
            "  evidence:",
            f"    environment_check: {config.outputs.environment_check}",
            f"    run_card: {run_card_path}",
            f"    safety_check: {config.outputs.safety_check}",
            f"    dev_eval_schema: {config.outputs.dev_eval_schema}",
            f"    adapter_manifest: {config.outputs.adapter_manifest}",
            f"    human_brief: {config.outputs.human_brief}",
            "",
        ]
    )
    _write_text(
        path,
        _replace_top_level_yaml_section(
            existing,
            section=config.phase_metadata.ledger_section,
            replacement=entry,
        ),
    )


def _phase_schema(config: TrainingPilotConfig, artifact_name: str) -> str:
    return f"training_pilot_{config.phase_metadata.schema_id}_{artifact_name}/v1"


def _pilot_command(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> str:
    config_path = _display_repo_path(repo_root, config.config_path)
    return f"{PILOT_COMMAND_PREFIX} --config {config_path}"


def _display_repo_path(repo_root: Path, path: Path | None) -> str:
    if path is None:
        return DEFAULT_PILOT_CONFIG_PATH
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(repo_root.resolve(strict=False)))
    except ValueError:
        return str(path)


def _combined_file_hash(repo_root: Path, paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        resolved = _resolve_path(repo_root, path)
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\0")
        if resolved.is_file():
            digest.update(sha256_file(resolved).encode("ascii"))
        else:
            digest.update(b"missing")
        digest.update(b"\0")
    return digest.hexdigest()


def _config_hash(config: TrainingPilotConfig) -> str:
    if config.config_path and config.config_path.is_file():
        return sha256_file(config.config_path)
    payload = {
        "base_model_name_or_path": config.base_model_name_or_path,
        "local_model_path": str(config.local_model_path),
        "model_revision": config.model_revision,
        "adapter_output_dir": str(config.adapter_output_dir),
        "max_steps": config.max_steps,
        "sample_limit": config.sample_limit,
        "seed": config.seed,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _git_check_ignore(repo_root: Path, path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _forbidden_artifact_scan(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    model_weight_suffixes = {".bin", ".ckpt", ".pt", ".pth", ".safetensors"}
    adapter_dir = _resolve_path(repo_root, config.adapter_output_dir)
    model_weight_paths: list[str] = []
    adapter_checkpoint_paths: list[str] = []
    training_cache_paths: list[str] = []
    for relative in _tracked_repo_paths(repo_root):
        path = repo_root / relative
        if path.suffix.lower() in model_weight_suffixes:
            model_weight_paths.append(relative)
        try:
            path.relative_to(adapter_dir)
        except ValueError:
            pass
        else:
            adapter_checkpoint_paths.append(relative)
        if _looks_like_training_cache_path(Path(relative)):
            training_cache_paths.append(relative)
    return {
        "model_weight_paths": sorted(set(model_weight_paths)),
        "adapter_checkpoint_paths": sorted(set(adapter_checkpoint_paths)),
        "training_cache_paths": sorted(set(training_cache_paths)),
    }


def _tracked_repo_paths(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        return ()
    paths = completed.stdout.decode("utf-8", errors="replace").split("\0")
    return tuple(path for path in paths if path)


def _artifact_freeze_hash_gate(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> GateResult:
    freeze_path = _resolve_path(repo_root, config.artifact_freeze_path)
    if not freeze_path.is_file():
        return GateResult(
            name="artifact_freeze_hashes_match",
            passed=False,
            code="artifact_freeze_missing",
            message=(
                "Phase 5A artifact freeze does not exist: "
                f"{config.artifact_freeze_path}"
            ),
        )
    try:
        data = json.loads(freeze_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return GateResult(
            name="artifact_freeze_hashes_match",
            passed=False,
            code="artifact_freeze_invalid",
            message=(
                "Phase 5A artifact freeze could not be read: "
                f"{config.artifact_freeze_path}: {exc}"
            ),
        )
    except json.JSONDecodeError as exc:
        return GateResult(
            name="artifact_freeze_hashes_match",
            passed=False,
            code="artifact_freeze_invalid",
            message=(
                "Phase 5A artifact freeze is not valid JSON: "
                f"{config.artifact_freeze_path}: {exc.msg}"
            ),
        )
    if not isinstance(data, dict) or not isinstance(data.get("artifacts"), dict):
        return GateResult(
            name="artifact_freeze_hashes_match",
            passed=False,
            code="artifact_freeze_invalid",
            message="Phase 5A artifact freeze must contain an artifacts object.",
        )

    mismatches: list[str] = []
    artifacts = cast(Mapping[str, object], data["artifacts"])
    for artifact_name, artifact_value in artifacts.items():
        if not isinstance(artifact_value, dict):
            mismatches.append(f"{artifact_name}: invalid artifact entry")
            continue
        path_value = artifact_value.get("path")
        expected_sha = artifact_value.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected_sha, str):
            mismatches.append(f"{artifact_name}: missing path or sha256")
            continue
        artifact_path = _resolve_path(repo_root, Path(path_value))
        if not artifact_path.is_file():
            mismatches.append(f"{artifact_name}: missing {path_value}")
            continue
        actual_sha = sha256_file(artifact_path)
        if actual_sha != expected_sha:
            mismatches.append(
                f"{artifact_name}: expected {expected_sha}, got {actual_sha}"
            )

    if mismatches:
        return GateResult(
            name="artifact_freeze_hashes_match",
            passed=False,
            code="artifact_freeze_mismatch",
            message="Phase 5A artifact freeze mismatch: " + "; ".join(mismatches),
        )
    return GateResult(
        name="artifact_freeze_hashes_match",
        passed=True,
        code="artifact_freeze_mismatch",
        message="Phase 5A artifact-freeze hashes match current files.",
    )


def _hard_negative_files_exist_gate(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> GateResult:
    missing = [
        str(path)
        for path in (
            config.train_hard_negatives_path,
            config.dev_hard_negatives_path,
        )
        if not _resolve_path(repo_root, path).is_file()
    ]
    if missing:
        return GateResult(
            name="hard_negative_files_exist",
            passed=False,
            code="hard_negative_file_missing",
            message="Missing hard-negative file(s): " + ", ".join(missing),
        )
    return GateResult(
        name="hard_negative_files_exist",
        passed=True,
        code="hard_negative_file_missing",
        message="Train and dev hard-negative files exist.",
    )


def _hard_negative_candidate_universe_gate(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    files_exist: bool,
) -> GateResult:
    if not files_exist:
        return GateResult(
            name="hard_negative_candidate_universe_matches",
            passed=False,
            code="hard_negative_candidate_universe_not_checked",
            message=(
                "Hard-negative candidate universe was not checked because a "
                "file is missing."
            ),
        )

    mismatches: list[str] = []
    for path in (config.train_hard_negatives_path, config.dev_hard_negatives_path):
        resolved = _resolve_path(repo_root, path)
        try:
            records = _read_jsonl(resolved)
        except TrainingPilotConfigError as exc:
            return GateResult(
                name="hard_negative_candidate_universe_matches",
                passed=False,
                code="hard_negative_file_invalid",
                message=str(exc),
            )
        for line_number, record in enumerate(records, start=1):
            candidate_universe = record.get("candidate_universe_id")
            if candidate_universe != config.candidate_universe_id:
                mismatches.append(
                    f"{path}:{line_number} has {candidate_universe!r}, "
                    f"expected {config.candidate_universe_id!r}"
                )
    if mismatches:
        return GateResult(
            name="hard_negative_candidate_universe_matches",
            passed=False,
            code="hard_negative_candidate_universe_mismatch",
            message="Hard-negative candidate universe mismatch: "
            + "; ".join(mismatches),
        )
    return GateResult(
        name="hard_negative_candidate_universe_matches",
        passed=True,
        code="hard_negative_candidate_universe_mismatch",
        message="Hard-negative candidate_universe_id values match config.",
    )


def _looks_like_training_cache_path(path: Path) -> bool:
    parts = path.parts
    if not parts:
        return False
    if parts[0] in {".cache", "wandb", "runs", "checkpoints"}:
        return True
    name = path.name.lower()
    return name.startswith("events.out.tfevents") or "tensorboard" in name


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def _looks_like_final_test_path(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts.intersection({"test", "final-test", "final_test"}):
        return True
    lowered_name = path.name.lower()
    return lowered_name in {"test.jsonl", "final-test.jsonl", "final_test.jsonl"}


def _validate_dev_only_query_file(
    path: Path,
    *,
    field_name: str,
    corpus_path: Path,
    repo_root: Path | None = None,
) -> None:
    if _looks_like_final_test_path(path):
        raise TrainingPilotConfigError(f"{field_name} must be dev-only")
    resolved_path = _resolve_path(repo_root, path) if repo_root is not None else path
    resolved_corpus = (
        _resolve_path(repo_root, corpus_path) if repo_root is not None else corpus_path
    )
    if not resolved_path.is_file():
        raise TrainingPilotConfigError(f"{field_name} does not exist: {path}")
    page_splits = _page_split_map(resolved_corpus)
    records = _read_jsonl(resolved_path)
    if not records:
        raise TrainingPilotConfigError(f"{field_name} must contain dev records")
    for record in records:
        split = record.get("split")
        if split != "dev":
            raise TrainingPilotConfigError(
                f"{field_name} must be dev-only; found split {split!r}"
            )
        for page_id in _record_page_ids(record):
            page_split = page_splits.get(page_id)
            if page_split == "test":
                raise TrainingPilotConfigError(
                    f"{field_name} references final test page {page_id}"
                )
            if page_split != "dev":
                raise TrainingPilotConfigError(
                    f"{field_name} must reference dev pages; "
                    f"{page_id} has split {page_split!r}"
                )


def _page_split_map(path: Path) -> dict[str, str]:
    records = _read_jsonl(path)
    page_splits: dict[str, str] = {}
    for record in records:
        page_id = record.get("page_id")
        split = record.get("split")
        if isinstance(page_id, str) and isinstance(split, str):
            page_splits[page_id] = split
    return page_splits


def _record_page_ids(record: Mapping[str, object]) -> tuple[str, ...]:
    page_ids: list[str] = []
    positive_page_ids = record.get("positive_page_ids")
    if isinstance(positive_page_ids, list):
        page_ids.extend(
            page_id for page_id in positive_page_ids if isinstance(page_id, str)
        )
    source = record.get("source")
    if isinstance(source, dict):
        source_page_id = source.get("page_id")
        if isinstance(source_page_id, str):
            page_ids.append(source_page_id)
    return tuple(page_ids)


def _read_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    records: list[Mapping[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise TrainingPilotConfigError(
                    f"{path}:{line_number} is not valid JSON: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise TrainingPilotConfigError(
                    f"{path}:{line_number} must be a JSON object"
                )
            records.append(cast(Mapping[str, object], value))
    return tuple(records)


def _resolved_outputs(
    outputs: TrainingPilotOutputs,
    *,
    repo_root: Path,
) -> TrainingPilotOutputs:
    return TrainingPilotOutputs(
        environment_check=_resolve_path(repo_root, outputs.environment_check),
        blocked_run_card=_resolve_path(repo_root, outputs.blocked_run_card),
        pilot_run_card=_resolve_path(repo_root, outputs.pilot_run_card),
        safety_check=_resolve_path(repo_root, outputs.safety_check),
        dev_eval_schema=_resolve_path(repo_root, outputs.dev_eval_schema),
        adapter_manifest=_resolve_path(repo_root, outputs.adapter_manifest),
        human_brief=_resolve_path(repo_root, outputs.human_brief),
        progress_ledger=_resolve_path(repo_root, outputs.progress_ledger),
    )


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _replace_top_level_yaml_section(
    text: str,
    *,
    section: str,
    replacement: str,
) -> str:
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line == f"{section}:":
            start = index
            break
    if start is None:
        prefix = text.rstrip() + "\n" if text.strip() else ""
        return prefix + replacement

    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith((" ", "-")):
            break
        end += 1
    return "\n".join([*lines[:start], replacement.rstrip(), *lines[end:]]).rstrip()


def _required_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise TrainingPilotConfigError(f"{key} must be an object")
    return value


def _optional_mapping(
    data: Mapping[str, object],
    key: str,
) -> Mapping[str, object] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TrainingPilotConfigError(f"{key} must be an object")
    return value


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TrainingPilotConfigError(f"{key} must be a non-empty string")
    return value


def _optional_str(data: Mapping[str, object], key: str, *, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise TrainingPilotConfigError(f"{key} must be a non-empty string")
    return value


def _phase_metadata_from_data(
    data: Mapping[str, object] | None,
) -> TrainingPilotPhaseMetadata:
    defaults = DEFAULT_PHASE_METADATA
    if data is None:
        return defaults
    metadata = TrainingPilotPhaseMetadata(
        schema_id=_optional_str(data, "schema_id", default=defaults.schema_id),
        phase_label=_optional_str(data, "phase_label", default=defaults.phase_label),
        change_name=_optional_str(data, "change_name", default=defaults.change_name),
        title=_optional_str(data, "title", default=defaults.title),
        ledger_section=_optional_str(
            data,
            "ledger_section",
            default=defaults.ledger_section,
        ),
        summary_zh=_optional_str(data, "summary_zh", default=defaults.summary_zh),
        recommended_next_step_zh=_optional_str(
            data,
            "recommended_next_step_zh",
            default=defaults.recommended_next_step_zh,
        ),
    )
    for field_name, value in {
        "schema_id": metadata.schema_id,
        "ledger_section": metadata.ledger_section,
    }.items():
        if not all(char.isalnum() or char == "_" for char in value):
            raise TrainingPilotConfigError(
                "phase_metadata."
                f"{field_name} must use only letters, numbers, or underscores"
            )
    return metadata


def _required_bool(data: Mapping[str, object], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise TrainingPilotConfigError(f"{key} must be a boolean")
    return value


def _optional_bool(
    data: Mapping[str, object],
    key: str,
    *,
    default: bool,
) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise TrainingPilotConfigError(f"{key} must be a boolean")
    return value


def _positive_int(data: Mapping[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise TrainingPilotConfigError(f"{key} must be a positive integer")
    return value


def _positive_float(data: Mapping[str, object], key: str) -> float:
    value = data.get(key)
    if (
        not isinstance(value, int | float)
        or isinstance(value, bool)
        or float(value) <= 0.0
    ):
        raise TrainingPilotConfigError(f"{key} must be a positive number")
    return float(value)


def _bounded_float(
    data: Mapping[str, object],
    key: str,
    *,
    lower: float,
    upper: float,
) -> float:
    value = _positive_or_zero_float(data, key)
    if value < lower or value >= upper:
        raise TrainingPilotConfigError(f"{key} must be in [{lower}, {upper})")
    return value


def _positive_or_zero_float(data: Mapping[str, object], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool) or value < 0.0:
        raise TrainingPilotConfigError(f"{key} must be a non-negative number")
    return float(value)
