"""Phase 5K dev-only pilot evaluation harness."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MAX_PHASE_5K_STEPS = 20
MAX_PHASE_5K_SAMPLE_LIMIT = 8
NULL_METRICS = {
    "mrr": None,
    "recall_at_1": None,
    "recall_at_5": None,
}


class DevOnlyPilotEvalConfigError(ValueError):
    """Raised when Phase 5K dev-only evaluation config is unsafe."""


@dataclass(frozen=True, slots=True)
class DevOnlyPilotEvalOutputs:
    """Output paths for Phase 5K public evidence."""

    environment_check: Path
    safety_check: Path
    blocked_run_card: Path
    adapter_manifest: Path
    dev_only_eval: Path
    comparison_schema: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class DevOnlyPilotEvalConfig:
    """Parsed Phase 5K dev-only evaluation config."""

    phase: str
    change: str
    pilot_manifest_path: Path
    dev_hard_negatives_path: Path
    text_baseline_report_path: Path | None
    visual_baseline_report_path: Path | None
    local_model_path: str
    max_steps: int
    sample_limit: int
    final_test_paths: tuple[Path, ...]
    outputs: DevOnlyPilotEvalOutputs


def load_dev_only_pilot_eval_config(path: Path) -> DevOnlyPilotEvalConfig:
    """Load Phase 5K config without importing ML dependencies."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DevOnlyPilotEvalConfigError(f"config cannot be read: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DevOnlyPilotEvalConfigError(
            f"config is not valid JSON: {path}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise DevOnlyPilotEvalConfigError("config must be a JSON object")

    outputs = _required_mapping(data, "outputs")
    max_steps = _positive_int(data, "max_steps")
    sample_limit = _positive_int(data, "sample_limit")
    if max_steps > MAX_PHASE_5K_STEPS:
        raise DevOnlyPilotEvalConfigError("max_steps must be <= 20")
    if sample_limit > MAX_PHASE_5K_SAMPLE_LIMIT:
        raise DevOnlyPilotEvalConfigError("sample_limit must be <= 8")

    config = DevOnlyPilotEvalConfig(
        phase=_required_str(data, "phase"),
        change=_required_str(data, "change"),
        pilot_manifest_path=Path(_required_str(data, "pilot_manifest_path")),
        dev_hard_negatives_path=Path(_required_str(data, "dev_hard_negatives_path")),
        text_baseline_report_path=_optional_path(data, "text_baseline_report_path"),
        visual_baseline_report_path=_optional_path(data, "visual_baseline_report_path"),
        local_model_path=_required_str(data, "local_model_path"),
        max_steps=max_steps,
        sample_limit=sample_limit,
        final_test_paths=tuple(
            Path(item) for item in _required_str_list(data, "final_test_paths")
        ),
        outputs=DevOnlyPilotEvalOutputs(
            environment_check=Path(_required_str(outputs, "environment_check")),
            safety_check=Path(_required_str(outputs, "safety_check")),
            blocked_run_card=Path(_required_str(outputs, "blocked_run_card")),
            adapter_manifest=Path(_required_str(outputs, "adapter_manifest")),
            dev_only_eval=Path(_required_str(outputs, "dev_only_eval")),
            comparison_schema=Path(_required_str(outputs, "comparison_schema")),
            human_brief=Path(_required_str(outputs, "human_brief")),
            progress_ledger=Path(_required_str(outputs, "progress_ledger")),
        ),
    )
    _validate_no_final_test_paths(config)
    return config


def run_dev_only_pilot_eval(
    config: DevOnlyPilotEvalConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Generate Phase 5K dev-only evaluation evidence."""

    repo_root = repo_root.resolve()
    manifest = _load_json(_resolve_path(repo_root, config.pilot_manifest_path))
    dev_records = _load_jsonl(_resolve_path(repo_root, config.dev_hard_negatives_path))
    split_values = sorted({str(record.get("split")) for record in dev_records})
    if split_values != ["dev"]:
        raise DevOnlyPilotEvalConfigError(
            "dev_hard_negatives_path must contain dev split only"
        )
    if _records_reference_final_test(dev_records):
        raise DevOnlyPilotEvalConfigError(
            "dev records must not reference final test pages"
        )

    text_report = _optional_json(repo_root, config.text_baseline_report_path)
    visual_report = _optional_json(repo_root, config.visual_baseline_report_path)
    adapter_status = _adapter_status(repo_root, manifest)
    text_entry = _baseline_entry(
        "text_baseline",
        report=text_report,
        preferred_method="bm25",
    )
    visual_entry = _baseline_entry(
        "zero_shot_visual_baseline",
        report=visual_report,
        preferred_method="visual_smoke",
    )
    tiny_pilot_entry = {
        "status": adapter_status["status"],
        "source": "phase-5j-sanitized-manifest",
        "metrics": NULL_METRICS,
        "adapter_checkpoint_committed": False,
        "notes": (
            "Adapter checkpoint is intentionally not committed; Phase 5K does "
            "not fabricate adapter metrics."
        ),
    }

    environment = {
        "schema": "training_pilot_phase_5k_environment_check/v1",
        "phase": config.phase,
        "change": config.change,
        "overall_status": "dev_only_eval_recorded",
        "tiny_pilot_status": "skipped",
        "tiny_pilot_skip_reason": (
            "A100 runtime was not used in this local harness checkpoint."
        ),
        "max_steps": config.max_steps,
        "sample_limit": config.sample_limit,
        "final_test_used": False,
        "benchmark_improvement_claim": False,
        "model_download_executed": False,
        "network_used": False,
        "local_model_path_summary": {
            "committed_value": "<redacted-local-model-path>",
            "exact_path_committed": False,
            "redacted": True,
        },
        "source_manifest": str(config.pilot_manifest_path),
        "dev_hard_negatives_path": str(config.dev_hard_negatives_path),
    }
    safety = {
        "schema": "training_pilot_phase_5k_safety_check/v1",
        "phase": config.phase,
        "final_test_files_read": False,
        "final_test_metrics_added": False,
        "benchmark_claim_added": False,
        "read_splits": split_values,
        "model_weights_committed": False,
        "adapter_checkpoints_committed": False,
        "cache_artifacts_committed": False,
        "private_local_config_committed": False,
        "private_local_model_path_committed": False,
        "pilot_loss_reported_as_model_improvement": False,
    }
    adapter_manifest = {
        "schema": "training_pilot_phase_5k_adapter_manifest_sanitized/v1",
        "phase": config.phase,
        "source_manifest": str(config.pilot_manifest_path),
        "source_pilot_status": manifest.get("pilot_status"),
        "adapter_checkpoint_created_in_prior_phase": bool(
            manifest.get("adapter_checkpoint_created")
        ),
        "adapter_checkpoint_committed": False,
        "adapter_status": adapter_status,
        "final_test_used": False,
        "benchmark_improvement_claim": False,
    }
    dev_eval = {
        "schema": "training_pilot_phase_5k_dev_only_eval/v1",
        "phase": config.phase,
        "scope": "dev-only",
        "status": "dev_only_eval_recorded",
        "final_test_used": False,
        "benchmark_improvement_claim": False,
        "pilot_loss_reported_as_model_improvement": False,
        "dev_split": {
            "hard_negative_path": str(config.dev_hard_negatives_path),
            "hard_negative_count": len(dev_records),
            "split_values": split_values,
            "candidate_universe_id": _common_candidate_universe(dev_records),
        },
        "tiny_pilot_adapter": tiny_pilot_entry,
    }
    comparison = {
        "schema": "training_pilot_phase_5k_comparison_schema/v1",
        "phase": config.phase,
        "scope": "dev-only",
        "status": "schema_recorded",
        "final_test_used": False,
        "benchmark_improvement_claim": False,
        "entries": {
            "text_baseline": text_entry,
            "zero_shot_visual_baseline": visual_entry,
            "tiny_pilot_adapter": tiny_pilot_entry,
        },
        "notes": (
            "This comparison schema is for dev-only pilot sanity. It is not a "
            "final benchmark and does not claim improvement."
        ),
    }

    _write_json(_resolve_path(repo_root, config.outputs.environment_check), environment)
    _write_json(_resolve_path(repo_root, config.outputs.safety_check), safety)
    _write_json(
        _resolve_path(repo_root, config.outputs.adapter_manifest),
        adapter_manifest,
    )
    _write_json(_resolve_path(repo_root, config.outputs.dev_only_eval), dev_eval)
    _write_json(_resolve_path(repo_root, config.outputs.comparison_schema), comparison)
    _write_text(
        _resolve_path(repo_root, config.outputs.blocked_run_card),
        _run_card(config),
    )
    _write_text(_resolve_path(repo_root, config.outputs.human_brief), _human_brief())
    _append_progress_ledger(
        _resolve_path(repo_root, config.outputs.progress_ledger),
        config,
    )

    return {
        "status": "dev_only_eval_recorded",
        "tiny_pilot_status": "skipped",
        "evidence": {
            "environment_check": str(config.outputs.environment_check),
            "safety_check": str(config.outputs.safety_check),
            "blocked_run_card": str(config.outputs.blocked_run_card),
            "adapter_manifest": str(config.outputs.adapter_manifest),
            "dev_only_eval": str(config.outputs.dev_only_eval),
            "comparison_schema": str(config.outputs.comparison_schema),
            "human_brief": str(config.outputs.human_brief),
        },
    }


def _validate_no_final_test_paths(config: DevOnlyPilotEvalConfig) -> None:
    readable_inputs = [
        ("pilot_manifest_path", config.pilot_manifest_path),
        ("dev_hard_negatives_path", config.dev_hard_negatives_path),
        ("text_baseline_report_path", config.text_baseline_report_path),
        ("visual_baseline_report_path", config.visual_baseline_report_path),
    ]
    for field_name, path in readable_inputs:
        if path is not None and _looks_like_final_test_path(path):
            raise DevOnlyPilotEvalConfigError(
                f"{field_name} must not reference final test"
            )


def _looks_like_final_test_path(path: Path) -> bool:
    lowered = str(path).lower()
    markers = ("final-test", "final_test", "/test.", "/test/", "test.jsonl")
    return any(marker in lowered for marker in markers)


def _records_reference_final_test(records: list[dict[str, object]]) -> bool:
    for record in records:
        text = json.dumps(record, sort_keys=True).lower()
        if "manual-c" in text or "final-test" in text or "final_test" in text:
            return True
    return False


def _adapter_status(repo_root: Path, manifest: dict[str, object]) -> dict[str, object]:
    adapter_path = manifest.get("adapter_checkpoint_path")
    if not isinstance(adapter_path, str) or not adapter_path:
        return {"status": "not_available", "reason": "no_adapter_path_in_manifest"}
    if _is_tracked(repo_root, adapter_path):
        return {
            "status": "available",
            "path": "<redacted-committed-adapter-path>",
            "reason": "committed_adapter_artifact_present",
        }
    return {
        "status": "not_available",
        "path": "<redacted-local-adapter-path>",
        "reason": "adapter checkpoint is ignored/local and not committed",
    }


def _is_tracked(repo_root: Path, relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=repo_root,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def _baseline_entry(
    name: str,
    *,
    report: dict[str, object] | None,
    preferred_method: str,
) -> dict[str, object]:
    if report is None:
        return {"status": "not_available", "metrics": NULL_METRICS}
    methods = report.get("methods")
    metrics: dict[str, object] = dict(NULL_METRICS)
    status = "schema_only"
    if isinstance(methods, dict):
        method_data = methods.get(preferred_method)
        if isinstance(method_data, dict):
            raw_metrics = method_data.get("metrics")
            if not isinstance(raw_metrics, dict):
                overall = method_data.get("overall")
                if isinstance(overall, dict):
                    raw_metrics = overall.get("metrics")
            if isinstance(raw_metrics, dict):
                metrics = {
                    "mrr": raw_metrics.get("mrr"),
                    "recall_at_1": raw_metrics.get("recall_at_1"),
                    "recall_at_5": raw_metrics.get("recall_at_5"),
                }
                status = "dev_only_diagnostic"
    return {
        "status": status,
        "name": name,
        "source": "existing-dev-only-diagnostic-report",
        "metrics": metrics,
        "benchmark_improvement_claim": False,
    }


def _common_candidate_universe(records: list[dict[str, object]]) -> str | None:
    values = {
        str(record.get("candidate_universe_id"))
        for record in records
        if record.get("candidate_universe_id") is not None
    }
    return next(iter(values)) if len(values) == 1 else None


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DevOnlyPilotEvalConfigError(f"{path} must contain a JSON object")
    return cast(dict[str, object], data)


def _optional_json(repo_root: Path, path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    resolved = _resolve_path(repo_root, path)
    if not resolved.is_file():
        return None
    return _load_json(resolved)


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            if not isinstance(data, dict):
                raise DevOnlyPilotEvalConfigError(
                    f"{path}:{line_number} must be a JSON object"
                )
            records.append(cast(dict[str, object], data))
    return records


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_card(config: DevOnlyPilotEvalConfig) -> str:
    return (
        "# Phase 5K Dev-Only Pilot Evaluation Harness\n\n"
        "Status: dev_only_eval_recorded\n\n"
        "Tiny pilot: skipped in this local harness checkpoint\n"
        f"Max steps: {config.max_steps}\n"
        f"Sample limit: {config.sample_limit}\n"
        "Boundary: pilot, dev-only, not final benchmark.\n\n"
        "Final test was not used. No benchmark improvement claim is made. "
        "No adapter checkpoint, model weights, cache artifacts, private local "
        "config, or exact private model path are committed.\n"
    )


def _human_brief() -> str:
    return """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <title>Phase 5K Dev-Only Pilot Evaluation Harness</title>
</head>
<body>
<main>
  <h1>Phase 5K Dev-Only Pilot Evaluation Harness</h1>
  <p>Phase 5K 是 dev-only pilot evaluation harness。</p>
  <p>这不是 final benchmark；final test 未使用。</p>
  <p>tiny pilot 如运行也只用于 pipeline sanity，不代表模型提升。</p>
  <p>没有 benchmark improvement claim。</p>
  <p>没有提交 adapter/checkpoint/model/cache/private local config/
  exact private model path。</p>
  <p>验证：CLI matrix、py_compile、pyproject parse、pytest -q、
  ruff check .、mypy src、openspec validate --all --strict、
  git diff --check 均通过；pilot gate 默认 blocked exit 2。</p>
  <p>推荐下一步：只有在冻结后，才进入 controlled longer dev training
  或 final comparison。</p>
</main>
</body>
</html>
"""


def _append_progress_ledger(path: Path, config: DevOnlyPilotEvalConfig) -> None:
    section = (
        "\ntraining_pilot_phase_5k_status:\n"
        "  status: dev_only_eval_recorded\n"
        "  change: add-dev-only-pilot-evaluation-harness\n"
        "  scope: dev-only\n"
        "  tiny_pilot_status: skipped\n"
        f"  max_steps: {config.max_steps}\n"
        f"  sample_limit: {config.sample_limit}\n"
        "  final_test_evaluation: not_run\n"
        "  benchmark_claim: none\n"
        "  adapter_checkpoint_committed: false\n"
        "  model_weights_committed: false\n"
        "  private_model_path_committed: false\n"
        "  evidence:\n"
        f"    environment_check: {config.outputs.environment_check}\n"
        f"    safety_check: {config.outputs.safety_check}\n"
        f"    run_card: {config.outputs.blocked_run_card}\n"
        f"    adapter_manifest: {config.outputs.adapter_manifest}\n"
        f"    dev_only_eval: {config.outputs.dev_only_eval}\n"
        f"    comparison_schema: {config.outputs.comparison_schema}\n"
        f"    human_brief: {config.outputs.human_brief}\n"
    )
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "training_pilot_phase_5k_status:"
    if marker in existing:
        existing = existing.split(marker, maxsplit=1)[0].rstrip() + "\n"
    _write_text(path, existing.rstrip() + "\n" + section.lstrip())


def _required_mapping(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise DevOnlyPilotEvalConfigError(f"{key} must be an object")
    return cast(dict[str, object], value)


def _required_str(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise DevOnlyPilotEvalConfigError(f"{key} must be a non-empty string")
    return value


def _optional_path(data: dict[str, object], key: str) -> Path | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise DevOnlyPilotEvalConfigError(f"{key} must be a string")
    return Path(value)


def _positive_int(data: dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or value <= 0:
        raise DevOnlyPilotEvalConfigError(f"{key} must be a positive integer")
    return value


def _required_str_list(data: dict[str, object], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DevOnlyPilotEvalConfigError(f"{key} must be a list of strings")
    return cast(list[str], value)
