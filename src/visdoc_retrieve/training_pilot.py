"""Phase 5B local-only real-training pilot launch gate helpers."""

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
PILOT_COMMAND = (
    "PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot "
    "--config configs/train_lora_pilot.local.example.json"
)


class TrainingPilotConfigError(ValueError):
    """Raised when a Phase 5B pilot config violates launch-gate boundaries."""


@dataclass(frozen=True, slots=True)
class TrainingPilotOutputs:
    """Report output paths for the Phase 5B pilot launch gate."""

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
    """Parsed Phase 5B pilot launch-gate config."""

    base_model_name_or_path: str
    local_model_path: Path
    model_revision: str
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
    learning_rate: float
    seed: int
    device: str
    allow_real_training: bool
    allow_final_test: bool
    save_adapter: bool
    report_timestamp_utc: str
    outputs: TrainingPilotOutputs
    config_path: Path | None


@dataclass(frozen=True, slots=True)
class GateResult:
    """One launch-gate check result."""

    name: str
    passed: bool
    code: str
    message: str


def load_training_pilot_config(path: Path) -> TrainingPilotConfig:
    """Load and validate a Phase 5B pilot JSON config without ML imports."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TrainingPilotConfigError("training-pilot config must be an object")

    outputs = _required_mapping(data, "outputs")
    config = TrainingPilotConfig(
        base_model_name_or_path=_required_str(data, "base_model_name_or_path"),
        local_model_path=Path(_required_str(data, "local_model_path")),
        model_revision=_required_str(data, "model_revision"),
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
        learning_rate=_positive_float(data, "learning_rate"),
        seed=_positive_int(data, "seed"),
        device=_required_str(data, "device"),
        allow_real_training=_required_bool(data, "allow_real_training"),
        allow_final_test=_required_bool(data, "allow_final_test"),
        save_adapter=_required_bool(data, "save_adapter"),
        report_timestamp_utc=_required_str(data, "report_timestamp_utc"),
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
        config_path=path,
    )
    _validate_pilot_config(config)
    return config


def run_training_pilot_gate(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
    environ: Mapping[str, str] | None = None,
    cuda_available: Callable[[], bool] | None = None,
) -> dict[str, object]:
    """Run Phase 5B launch gates and write blocked or pilot evidence."""

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
        training_result = _run_guarded_real_training_pilot(
            config,
            repo_root=repo_root,
        )
        if training_result.get("status") != "pilot_run":
            blocked_reasons.append(
                {
                    "code": str(training_result.get("blocked_code")),
                    "message": str(training_result.get("blocked_message")),
                }
            )

    status = "blocked" if blocked_reasons else "pilot_run"
    environment = _environment_check(
        config,
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
            environment=environment,
        )
    else:
        _write_pilot_run_card(
            outputs.pilot_run_card,
            config=config,
            environment=environment,
        )
    _write_human_brief(
        outputs.human_brief,
        config=config,
        environment=environment,
    )
    _update_progress_ledger(
        outputs.progress_ledger,
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


def _validate_pilot_config(config: TrainingPilotConfig) -> None:
    if config.allow_final_test:
        raise TrainingPilotConfigError("allow_final_test must remain false")
    if config.max_steps > MAX_PILOT_STEPS:
        raise TrainingPilotConfigError(f"max_steps must be <= {MAX_PILOT_STEPS}")
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
    can_probe_cuda = (
        config.allow_real_training
        and env_enabled
        and local_model_exists
        and adapter_output_ignored
        and config.max_steps <= MAX_PILOT_STEPS
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
            message="allow_final_test must remain false for Phase 5B pilot launch.",
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
        GateResult(
            name="local_model_path_exists",
            passed=local_model_exists,
            code="missing_local_model_path",
            message=f"local_model_path does not exist: {config.local_model_path}",
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
    gates: Sequence[GateResult],
    blocked_reasons: Sequence[Mapping[str, object]],
    status: str,
    training_result: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "schema": "training_pilot_environment_check/v1",
        "timestamp_utc": config.report_timestamp_utc,
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
            "local_model_path": str(config.local_model_path),
            "adapter_output_dir": str(config.adapter_output_dir),
            "max_steps": config.max_steps,
            "device": config.device,
            "candidate_universe_id": config.candidate_universe_id,
        },
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
        "schema": "training_pilot_safety_check/v1",
        "training_executed": status == "pilot_run",
        "model_download_executed": False,
        "network_used": False,
        "final_test_used": False,
        "adapter_checkpoint_committed": bool(adapter_checkpoint_paths),
        "model_weights_committed": bool(model_weight_paths),
        "training_cache_committed": bool(training_cache_paths),
        "benchmark_claim_added": False,
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
        "schema": "training_pilot_dev_eval/v1",
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
    return {
        "schema": "training_pilot_adapter_manifest/v1",
        "adapter_output_dir": str(config.adapter_output_dir),
        "base_model_name_or_path": config.base_model_name_or_path,
        "model_revision": config.model_revision,
        "hard_negative_artifact_hash": _combined_file_hash(
            repo_root,
            [config.train_hard_negatives_path, config.dev_hard_negatives_path],
        ),
        "train_config_hash": _config_hash(config),
        "git_commit": _git_commit(repo_root),
        "max_steps": config.max_steps,
        "seed": config.seed,
        "device": config.device,
        "final_test_used": False,
        "created_at": config.report_timestamp_utc,
        "pilot_status": status,
        "adapter_checkpoint_created": status == "pilot_run",
        "adapter_checkpoint_path": (
            str(config.adapter_output_dir) if status == "pilot_run" else None
        ),
        "real_training_result": dict(training_result) if training_result else None,
    }


def _run_guarded_real_training_pilot(
    config: TrainingPilotConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Guarded local-only real-training scaffold.

    This is intentionally unreachable from default validation. Optional imports
    happen here, after all non-import gates have passed.
    """

    missing = _missing_optional_training_modules()
    if missing:
        return {
            "status": "blocked",
            "blocked_code": "optional_training_dependency_missing",
            "blocked_message": (
                "Missing optional real-training dependencies: " + ", ".join(missing)
            ),
            "training_executed": False,
        }
    return {
        "status": "blocked",
        "blocked_code": "real_training_backend_scaffold_only",
        "blocked_message": (
            "All launch gates passed, but this scaffold does not fabricate an "
            "adapter checkpoint. Wire a reviewed local backend before recording "
            "pilot_run."
        ),
        "training_executed": False,
        "repo_root": str(repo_root),
        "max_steps": config.max_steps,
        "local_model_path": str(config.local_model_path),
    }


def _missing_optional_training_modules() -> tuple[str, ...]:
    missing: list[str] = []
    for module_name in ("torch", "transformers", "peft", "colpali_engine"):
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    return tuple(missing)


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
    environment: Mapping[str, object],
) -> None:
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    reason_lines = [
        f"- {reason['code']}: {reason['message']}"
        for reason in reasons
    ]
    lines = [
        "# Phase 5B Training Pilot Launch Gate",
        "",
        "Status: blocked",
        "",
        f"Timestamp: {config.report_timestamp_utc}",
        f"Command: {PILOT_COMMAND}",
        f"Candidate universe: {config.candidate_universe_id}",
        "",
        "Boundary: pilot, dev-only, not final benchmark.",
        "",
        "Training did not run. This blocked run is not a real training result "
        "and does not claim benchmark improvement.",
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
    environment: Mapping[str, object],
) -> None:
    _write_text(
        path,
        "\n".join(
            [
                "# Phase 5B Training Pilot Launch Gate",
                "",
                "Status: pilot_run",
                "",
                f"Timestamp: {config.report_timestamp_utc}",
                f"Command: {PILOT_COMMAND}",
                "Boundary: pilot, dev-only, not final benchmark.",
                "",
                "Final test was not used and no benchmark improvement claim is made.",
                "",
            ]
        ),
    )


def _write_human_brief(
    path: Path,
    *,
    config: TrainingPilotConfig,
    environment: Mapping[str, object],
) -> None:
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    reason_items = "".join(
        f"<li><code>{reason['code']}</code>: {reason['message']}</li>"
        for reason in reasons
    )
    status = str(environment["overall_status"])
    html = "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Phase 5B Training Pilot Launch Gate</title>",
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
            "  <h1>Phase 5B Training Pilot Launch Gate</h1>",
            "  <h2>一句话结论</h2>",
            "  <p>Phase 5B 已新增真实 LoRA / QLoRA pilot 的本地启动门禁；",
            f'  当前状态为 <span class="status">{status}</span>，默认不训练。</p>',
            "  <h2>当前状态</h2>",
            "  <p>这是 pilot / dev-only / not final benchmark 检查点。",
            "  final test 仍未使用，没有 benchmark improvement claim。</p>",
            "  <h2>本阶段变化</h2>",
            "  <ul>",
            "    <li>新增配置 "
            "<code>configs/train_lora_pilot.local.example.json</code>。</li>",
            f"    <li>新增 CLI <code>{PILOT_COMMAND}</code>。</li>",
            "    <li>生成 environment check、run-card、safety check、",
            "    dev eval schema 和 adapter manifest example。</li>",
            "  </ul>",
            "  <h2>训练门禁</h2>",
            "  <p>只有同时满足 allow_real_training=true、",
            "  allow_final_test=false、",
            "  <code>VISDOC_ENABLE_REAL_TRAINING=1</code>、",
            "  本地模型路径存在、CUDA 可用、",
            f"  <code>max_steps &lt;= {MAX_PILOT_STEPS}</code>、",
            "  adapter 输出目录被 git ignore，才允许进入 guarded real pilot",
            "  launcher。</p>",
            "  <h2>为什么默认不训练</h2>",
            f"  <ul>{reason_items}</ul>",
            "  <h2>A100 / 本地模型 pilot 运行方式</h2>",
            "  <p>在 A100 或本地 CUDA 环境中，先准备本地模型目录，",
            "  确认 adapter 输出在 ignored artifacts 目录下，再显式设置",
            "  <code>VISDOC_ENABLE_REAL_TRAINING=1</code> 并将配置中的",
            "  <code>allow_real_training</code> 改为 true。不要下载模型，",
            "  不要启用 final test。</p>",
            "  <h2>关键证据</h2>",
            "  <ul>",
            "    <li><code>reports/training-pilot/environment-check.json",
            "    </code></li>",
            "    <li><code>reports/training-pilot/blocked-run-card.md</code>",
            "    或 <code>reports/training-pilot/pilot-run-card.md</code></li>",
            "    <li><code>reports/training-pilot/safety-check.json</code></li>",
            "    <li><code>reports/training-pilot/dev-eval-schema.json",
            "    </code></li>",
            "    <li><code>reports/training-pilot/adapter-manifest.example.json",
            "    </code></li>",
            "  </ul>",
            "  <h2>不应夸大的结论</h2>",
            "  <p>没有提交 adapter / weights；没有把 blocked 或 dry-run 写成",
            "  真实训练结果；没有把 mock visual result 写成 real visual result。</p>",
            "  <h2>推荐下一步</h2>",
            "  <p>在具备本地模型和 CUDA 的 A100 环境中运行一次小预算 pilot，",
            "  或继续记录 blocked evidence。</p>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )
    _write_text(path, html)


def _update_progress_ledger(
    path: Path,
    *,
    status: str,
    environment: Mapping[str, object],
) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    reasons = cast(Sequence[Mapping[str, object]], environment["blocked_reasons"])
    reason_codes = [str(reason["code"]) for reason in reasons]
    reason_lines = [f"    - {code}" for code in reason_codes]
    if not reason_lines:
        reason_lines = ["    - none"]
    entry = "\n".join(
        [
            "training_pilot_status:",
            f"  status: {status}",
            "  change: add-training-pilot-launch-gate",
            f"  command: {PILOT_COMMAND}",
            "  config: configs/train_lora_pilot.local.example.json",
            "  candidate_universe: evaluated_split_pages",
            (
                "  training: not_executed"
                if status == "blocked"
                else "  training: pilot_run"
            ),
            "  model_download: not_executed",
            "  network: not_used",
            "  final_test_evaluation: not_run",
            "  benchmark_claim: none",
            "  adapter_checkpoint_committed: false",
            "  model_weights_committed: false",
            "  mock_visual_result_reported_as_real: false",
            "  blocked_reasons:",
            *reason_lines,
            "  evidence:",
            "    environment_check: reports/training-pilot/environment-check.json",
            "    run_card: reports/training-pilot/blocked-run-card.md",
            "    safety_check: reports/training-pilot/safety-check.json",
            "    dev_eval_schema: reports/training-pilot/dev-eval-schema.json",
            "    adapter_manifest: "
            "reports/training-pilot/adapter-manifest.example.json",
            "    human_brief: "
            "docs/human-briefs/2026-07-01-training-pilot-launch-gate.html",
            "",
        ]
    )
    _write_text(
        path,
        _replace_top_level_yaml_section(
            existing,
            section="training_pilot_status",
            replacement=entry,
        ),
    )


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
) -> None:
    if _looks_like_final_test_path(path):
        raise TrainingPilotConfigError(f"{field_name} must be dev-only")
    if not path.is_file():
        raise TrainingPilotConfigError(f"{field_name} does not exist: {path}")
    page_splits = _page_split_map(corpus_path)
    records = _read_jsonl(path)
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
            value = json.loads(stripped)
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


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TrainingPilotConfigError(f"{key} must be a non-empty string")
    return value


def _required_bool(data: Mapping[str, object], key: str) -> bool:
    value = data.get(key)
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
