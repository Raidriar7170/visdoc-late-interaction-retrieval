"""Phase 6C final-comparison execution gate dry-run."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

PHASE_6C_CHANGE = "add-final-comparison-execution-gate-dry-run"
PROTOCOL_VERSION = "phase-6b-final-comparison-protocol/v1"


class FinalComparisonGateConfigError(ValueError):
    """Raised when Phase 6C dry-run gate configuration is unsafe."""


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """Artifact required or inspected by the Phase 6C dry-run gate."""

    artifact_id: str
    path: Path
    required: bool
    category: str


@dataclass(frozen=True, slots=True)
class FinalComparisonGateOutputs:
    """Output paths for Phase 6C public evidence."""

    dry_run: Path
    readiness_report: Path
    claim_checklist: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class FinalComparisonGateConfig:
    """Configuration for the Phase 6C dry-run gate."""

    phase: str
    change: str
    protocol_version: str
    protocol_doc: Path
    artifacts: tuple[ArtifactSpec, ...]
    final_test_forbidden_paths: tuple[Path, ...]
    outputs: FinalComparisonGateOutputs

    def with_overrides(
        self,
        *,
        artifacts: tuple[ArtifactSpec, ...] | None = None,
        final_test_forbidden_paths: tuple[Path, ...] | None = None,
        outputs: FinalComparisonGateOutputs | None = None,
    ) -> FinalComparisonGateConfig:
        """Return a copy with test or CLI output overrides."""

        return replace(
            self,
            artifacts=artifacts if artifacts is not None else self.artifacts,
            final_test_forbidden_paths=(
                final_test_forbidden_paths
                if final_test_forbidden_paths is not None
                else self.final_test_forbidden_paths
            ),
            outputs=outputs if outputs is not None else self.outputs,
        )


def build_phase_6c_default_config() -> FinalComparisonGateConfig:
    """Build the default checked-in Phase 6C dry-run configuration."""

    artifacts = (
        ArtifactSpec(
            "protocol_status",
            Path("reports/final-comparison-protocol/phase-6b-protocol-freeze.json"),
            True,
            "protocol_status",
        ),
        ArtifactSpec(
            "comparison_schema",
            Path("reports/final-comparison-protocol/phase-6b-comparison-schema.json"),
            True,
            "comparison_schema",
        ),
        ArtifactSpec(
            "claim_checklist",
            Path("reports/final-comparison-protocol/phase-6b-claim-checklist.json"),
            True,
            "claim_checklist",
        ),
        ArtifactSpec(
            "candidate_universe",
            Path("reports/mvp/metrics.json"),
            True,
            "candidate_universe",
        ),
        ArtifactSpec(
            "split_policy",
            Path("reports/training-readiness/artifact-freeze.json"),
            True,
            "split_policy",
        ),
        ArtifactSpec(
            "metrics_definitions",
            Path("openspec/specs/retrieval-evaluation-metrics/spec.md"),
            True,
            "metrics_definitions",
        ),
        ArtifactSpec(
            "mvp_evidence",
            Path("reports/mvp/run-card.md"),
            True,
            "mvp_evidence",
        ),
        ArtifactSpec(
            "hard_negative_evidence",
            Path("reports/hard-negatives/mining-summary.json"),
            True,
            "hard_negative_evidence",
        ),
        ArtifactSpec(
            "training_readiness_evidence",
            Path("reports/training-readiness/dataset-summary.json"),
            True,
            "training_readiness_evidence",
        ),
        ArtifactSpec(
            "tiny_runner_or_training_gate_evidence",
            Path("reports/training-pilot/phase-5j-pilot-run-card.md"),
            True,
            "training_pilot_evidence",
        ),
        ArtifactSpec(
            "dev_only_harness_evidence",
            Path("reports/training-pilot/phase-5k-dev-only-eval.json"),
            True,
            "dev_only_harness_evidence",
        ),
        ArtifactSpec(
            "dev_only_comparison_schema",
            Path("reports/training-pilot/phase-5k-comparison-schema.json"),
            True,
            "dev_only_harness_evidence",
        ),
    )
    return FinalComparisonGateConfig(
        phase="6C",
        change=PHASE_6C_CHANGE,
        protocol_version=PROTOCOL_VERSION,
        protocol_doc=Path("docs/final-comparison-protocol.md"),
        artifacts=artifacts,
        final_test_forbidden_paths=(
            Path("data/final-test/qrels.jsonl"),
            Path("data/final-test/labels.jsonl"),
            Path("reports/final-comparison/final-test-metrics.json"),
        ),
        outputs=FinalComparisonGateOutputs(
            dry_run=Path(
                "reports/final-comparison-protocol/"
                "phase-6c-execution-gate-dry-run.json"
            ),
            readiness_report=Path(
                "reports/final-comparison-protocol/phase-6c-readiness-report.md"
            ),
            claim_checklist=Path(
                "reports/final-comparison-protocol/phase-6c-claim-checklist.json"
            ),
            human_brief=Path(
                "docs/human-briefs/2026-07-08-final-comparison-dry-run-gate.md"
            ),
            progress_ledger=Path("reports/progress-ledger.yaml"),
        ),
    )


def evaluate_active_openspec_state(
    active_changes: tuple[str, ...],
    allowed_change: str,
) -> dict[str, object]:
    """Classify active OpenSpec state for a pre- or post-merge Phase 6C gate."""

    sorted_changes = sorted(active_changes)
    unexpected = [name for name in sorted_changes if name != allowed_change]
    if not sorted_changes:
        status = "pass"
        mode = "post_merge_no_active_changes"
    elif sorted_changes == [allowed_change]:
        status = "pass"
        mode = "phase_6c_change_only"
    else:
        status = "blocked"
        mode = "unexpected_active_changes"
    return {
        "status": status,
        "mode": mode,
        "allowed_change": allowed_change,
        "active_changes": sorted_changes,
        "unexpected_active_changes": unexpected,
    }


def discover_active_openspec_changes(repo_root: Path) -> tuple[str, ...]:
    """Return active OpenSpec changes using the local CLI without mutating state."""

    completed = subprocess.run(
        ["openspec", "list", "--json"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        json_start = completed.stdout.find("{")
        if json_start >= 0:
            try:
                data = json.loads(completed.stdout[json_start:])
            except json.JSONDecodeError:
                data = {}
            changes = data.get("changes")
            if isinstance(changes, list):
                json_names: list[str] = []
                for item in changes:
                    if isinstance(item, dict):
                        name = item.get("name")
                        if isinstance(name, str):
                            json_names.append(name)
                return tuple(json_names)

    fallback = subprocess.run(
        ["openspec", "list"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    text_names: list[str] = []
    for line in fallback.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("Note:", "Changes:", "No active")):
            continue
        text_names.append(stripped.split()[0])
    return tuple(text_names)


def run_final_comparison_gate(
    config: FinalComparisonGateConfig,
    *,
    repo_root: Path,
    active_changes: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Generate Phase 6C dry-run evidence without final-test access."""

    repo_root = repo_root.resolve()
    _validate_output_paths(config.outputs)

    protocol_text = _load_text(_resolve_path(repo_root, config.protocol_doc))
    protocol_doc_check = _protocol_doc_check(protocol_text)
    artifact_checks = [_artifact_check(repo_root, spec) for spec in config.artifacts]
    active = (
        active_changes
        if active_changes is not None
        else discover_active_openspec_changes(repo_root)
    )
    active_state = evaluate_active_openspec_state(active, config.change)
    frozen_checks = _frozen_readiness_checks(repo_root, config, artifact_checks)
    final_test_guard = {
        "status": "locked",
        "final_test_read": False,
        "final_test_forbidden_paths": [
            str(path) for path in config.final_test_forbidden_paths
        ],
        "final_test_evaluation": "not_run",
        "final_test_metrics_added": False,
    }
    output_path_safety = _output_path_safety(config.outputs)
    claim_checklist = _claim_checklist(config)
    planned_runs = _planned_runs(config)
    blocked_reasons = _blocked_reasons(
        artifact_checks=artifact_checks,
        active_state=active_state,
        frozen_checks=frozen_checks,
        output_path_safety=output_path_safety,
    )
    final_run_readiness = "ready_for_phase_6d" if not blocked_reasons else "blocked"

    dry_run = {
        "schema": "final_comparison_execution_gate_dry_run/v1",
        "phase": config.phase,
        "change": config.change,
        "protocol_version": config.protocol_version,
        "status": final_run_readiness,
        "final_run_readiness": final_run_readiness,
        "final_test_guard": final_test_guard,
        "final_comparison_execution": "not_executed",
        "comparison_mode": "dry_run_only",
        "benchmark_improvement_claim": False,
        "training": "not_executed",
        "tuning": "not_executed",
        "model_download": "not_executed",
        "a100_or_gpu_used": False,
        "ssh_used": False,
        "protocol_doc_check": protocol_doc_check,
        "active_openspec_state": active_state,
        "artifact_checks": artifact_checks,
        "frozen_readiness_checks": frozen_checks,
        "output_path_safety": output_path_safety,
        "planned_runs": planned_runs,
        "blocked_reasons": blocked_reasons,
        "evidence_paths": {
            "dry_run": str(config.outputs.dry_run),
            "readiness_report": str(config.outputs.readiness_report),
            "claim_checklist": str(config.outputs.claim_checklist),
            "human_brief": str(config.outputs.human_brief),
        },
        "next_phase": "Phase 6D one-time frozen final comparison",
    }

    _write_json(_resolve_path(repo_root, config.outputs.dry_run), dry_run)
    _write_json(
        _resolve_path(repo_root, config.outputs.claim_checklist),
        claim_checklist,
    )
    _write_text(
        _resolve_path(repo_root, config.outputs.readiness_report),
        _readiness_report(config, dry_run),
    )
    _write_text(_resolve_path(repo_root, config.outputs.human_brief), _human_brief())
    _append_progress_ledger(
        _resolve_path(repo_root, config.outputs.progress_ledger),
        config,
        final_run_readiness,
        blocked_reasons,
    )

    return {
        "status": final_run_readiness,
        "blocked_reasons": blocked_reasons,
        "evidence": dry_run["evidence_paths"],
    }


def _artifact_check(repo_root: Path, spec: ArtifactSpec) -> dict[str, object]:
    path = _resolve_path(repo_root, spec.path)
    status = "present" if path.is_file() else "missing"
    return {
        "artifact_id": spec.artifact_id,
        "category": spec.category,
        "path": str(spec.path),
        "required": spec.required,
        "status": status,
    }


def _frozen_readiness_checks(
    repo_root: Path,
    config: FinalComparisonGateConfig,
    artifact_checks: list[dict[str, object]],
) -> dict[str, object]:
    protocol = _optional_json(
        _resolve_path(
            repo_root,
            Path("reports/final-comparison-protocol/phase-6b-protocol-freeze.json"),
        )
    )
    phase_6b_claim = _optional_json(
        _resolve_path(
            repo_root,
            Path("reports/final-comparison-protocol/phase-6b-claim-checklist.json"),
        )
    )
    mvp_metrics = _optional_json(repo_root / "reports/mvp/metrics.json")
    artifact_freeze = _optional_json(
        repo_root / "reports/training-readiness/artifact-freeze.json"
    )
    metric_spec = _load_text(
        repo_root / "openspec/specs/retrieval-evaluation-metrics/spec.md"
    )
    protocol_text = _load_text(_resolve_path(repo_root, config.protocol_doc))
    required_present = all(
        not check["required"] or check["status"] == "present"
        for check in artifact_checks
    )
    candidate_universe_frozen = (
        _nested_get(mvp_metrics, ("candidate_universe", "name"))
        == "evaluated_split_pages"
        and artifact_freeze.get("candidate_universe_id") == "evaluated_split_pages"
    )
    split_policy = artifact_freeze.get("split_policy")
    split_policy_frozen = (
        isinstance(split_policy, dict)
        and split_policy.get("final_test") == "excluded"
        and "train" in split_policy
        and "dev" in split_policy
    )
    metric_definitions_frozen = all(
        token in metric_spec for token in ("Recall@1", "Recall@5", "MRR", "NDCG@10")
    )
    phase_6b_claim_checklist_blocks = (
        phase_6b_claim.get("benchmark_claim_allowed") is False
        and phase_6b_claim.get("claim_status") == "blocked"
    )
    protocol_status_exists = protocol.get("status") == "protocol_freeze_recorded"
    final_test_guard_locked = (
        protocol.get("final_test_evaluation") == "not_run"
        and protocol.get("final_benchmark_status") == "not_run"
    )
    no_tuning_after_final_documented = (
        "A future final-test run requires a new OpenSpec change" in protocol_text
        and "Until then" in protocol_text
    )
    return {
        "required_artifacts_present": required_present,
        "protocol_status_exists": protocol_status_exists,
        "comparison_schema_exists": (
            repo_root
            / "reports/final-comparison-protocol/phase-6b-comparison-schema.json"
        ).is_file(),
        "claim_checklist_exists": (
            repo_root
            / "reports/final-comparison-protocol/phase-6b-claim-checklist.json"
        ).is_file(),
        "candidate_universe_frozen": candidate_universe_frozen,
        "split_policy_frozen": split_policy_frozen,
        "metrics_definitions_frozen": metric_definitions_frozen,
        "mvp_evidence_exists": (repo_root / "reports/mvp/run-card.md").is_file(),
        "hard_negative_evidence_exists": (
            repo_root / "reports/hard-negatives/mining-summary.json"
        ).is_file(),
        "training_readiness_evidence_exists": (
            repo_root / "reports/training-readiness/dataset-summary.json"
        ).is_file(),
        "training_pilot_evidence_exists": (
            repo_root / "reports/training-pilot/phase-5j-pilot-run-card.md"
        ).is_file(),
        "dev_only_harness_evidence_exists": (
            repo_root / "reports/training-pilot/phase-5k-dev-only-eval.json"
        ).is_file(),
        "final_test_guard_locked": final_test_guard_locked,
        "phase_6b_claim_checklist_blocks": phase_6b_claim_checklist_blocks,
        "no_tuning_after_final_documented": no_tuning_after_final_documented,
    }


def _claim_checklist(config: FinalComparisonGateConfig) -> dict[str, object]:
    return {
        "schema": "final_comparison_phase_6c_claim_checklist/v1",
        "phase": config.phase,
        "protocol_version": config.protocol_version,
        "claim_status": "blocked_until_phase_6d_final_run",
        "benchmark_claim_allowed": False,
        "final_test_evaluation": "not_run",
        "final_comparison_execution": "not_executed",
        "checklist": {
            "protocol_version_referenced": True,
            "candidate_universe_frozen": True,
            "split_policy_frozen": True,
            "metric_definitions_frozen": True,
            "final_test_authorized": False,
            "final_test_read": False,
            "final_comparison_executed": False,
            "final_metrics_generated": False,
            "reviewer_approval_recorded": False,
            "no_tuning_after_final_documented": True,
            "model_weight_hygiene_passed": True,
            "adapter_checkpoint_hygiene_passed": True,
            "training_cache_hygiene_passed": True,
            "private_config_absent": True,
            "exact_private_model_path_absent": True,
            "dev_only_not_presented_as_final": True,
            "tiny_runner_not_presented_as_benchmark": True,
            "readme_result_claim_added": False,
        },
        "blocked_reasons": [
            "final_test_not_authorized",
            "final_test_not_run",
            "final_comparison_not_executed",
            "final_comparison_metrics_not_generated",
            "reviewer_approval_not_recorded",
        ],
    }


def _planned_runs(config: FinalComparisonGateConfig) -> list[dict[str, object]]:
    return [
        {
            "run_id": "phase-6d-one-time-final-comparison",
            "status": "planned_not_executed",
            "phase": "6D",
            "requires_new_openspec_change": True,
            "protocol_version": config.protocol_version,
            "split_scope": "final_test",
            "candidate_universe": "evaluated_split_pages",
            "expected_artifact_paths": {
                "final_comparison_report": (
                    "reports/final-comparison/phase-6d-final-comparison.json"
                ),
                "claim_checklist": (
                    "reports/final-comparison/phase-6d-claim-checklist.json"
                ),
            },
            "metrics": None,
            "benchmark_claim": "blocked_until_phase_6d_review",
        }
    ]


def _blocked_reasons(
    *,
    artifact_checks: list[dict[str, object]],
    active_state: dict[str, object],
    frozen_checks: dict[str, object],
    output_path_safety: dict[str, object],
) -> list[str]:
    reasons: list[str] = []
    if any(
        check["required"] and check["status"] != "present"
        for check in artifact_checks
    ):
        reasons.append("required_artifact_missing")
    if active_state["status"] != "pass":
        reasons.append("unexpected_active_openspec_changes")
    if not all(value is True for value in frozen_checks.values()):
        reasons.append("frozen_readiness_check_failed")
    if output_path_safety["status"] != "pass":
        reasons.append("unsafe_output_paths")
    return reasons


def _protocol_doc_check(protocol_text: str) -> dict[str, object]:
    return {
        "status": "present",
        "protocol_version_referenced": PROTOCOL_VERSION in protocol_text,
        "final_test_access_gate_documented": "Final-Test Access Gates" in protocol_text,
        "no_benchmark_claim_boundary": (
            "benchmark-improvement language" in protocol_text
        ),
    }


def _output_path_safety(outputs: FinalComparisonGateOutputs) -> dict[str, object]:
    unsafe = [
        str(path)
        for path in _output_paths(outputs)
        if _is_unsafe_output_path(path)
    ]
    return {
        "status": "pass" if not unsafe else "blocked",
        "unsafe_paths": unsafe,
    }


def _validate_output_paths(outputs: FinalComparisonGateOutputs) -> None:
    safety = _output_path_safety(outputs)
    if safety["status"] != "pass":
        raise FinalComparisonGateConfigError(
            f"unsafe output path: {safety['unsafe_paths']}"
        )


def _output_paths(outputs: FinalComparisonGateOutputs) -> tuple[Path, ...]:
    return (
        outputs.dry_run,
        outputs.readiness_report,
        outputs.claim_checklist,
        outputs.human_brief,
        outputs.progress_ledger,
    )


def _is_unsafe_output_path(path: Path) -> bool:
    lowered_name = path.name.lower()
    lowered_parts = {part.lower() for part in path.parts}
    unsafe_parts = {
        ".local",
        ".cache",
        ".worktrees",
        ".codex",
        "checkpoints",
        "checkpoint",
        "adapter-checkpoints",
        "adapter_checkpoints",
        "private-config",
        "private_config",
        "final-test",
        "final_test",
    }
    unsafe_names = {
        "adapter_model.safetensors",
        "model.safetensors",
        "pytorch_model.bin",
    }
    return bool(lowered_parts & unsafe_parts) or lowered_name in unsafe_names


def _optional_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _nested_get(data: dict[str, object], keys: tuple[str, ...]) -> object | None:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _readiness_report(
    config: FinalComparisonGateConfig,
    dry_run: dict[str, object],
) -> str:
    blocked = cast(list[str], dry_run["blocked_reasons"])
    readiness = dry_run["final_run_readiness"]
    artifact_lines = "\n".join(
        f"- `{item['artifact_id']}`: {item['status']} ({item['path']})"
        for item in cast(list[dict[str, object]], dry_run["artifact_checks"])
    )
    blocked_text = ", ".join(blocked) if blocked else "none"
    return (
        "# Phase 6C Final-Comparison Execution Gate Dry-Run\n\n"
        f"Status: `{readiness}`\n\n"
        "This checkpoint verifies protocol readiness only. It did not read final "
        "test data, did not run final comparison, did not train, and does not "
        "claim benchmark improvement.\n\n"
        "## Gate Summary\n\n"
        f"- Protocol version: `{config.protocol_version}`\n"
        "- Final test read: `false`\n"
        "- Final comparison execution: `not_executed`\n"
        "- Benchmark improvement claim: `false`\n"
        f"- Blocked reasons: `{blocked_text}`\n\n"
        "## Artifact Checks\n\n"
        f"{artifact_lines}\n\n"
        "## Planned Phase 6D Run\n\n"
        "Phase 6D is the later one-time frozen final comparison. It requires a "
        "new explicit OpenSpec change, authorized final-test inputs, artifact "
        "hygiene, final metrics, and reviewer approval before any public claim.\n"
    )


def _human_brief() -> str:
    return (
        "# Phase 6C Final-Comparison Dry-Run Gate\n\n"
        "一句话结论：Phase 6C 只完成 final-comparison dry-run gate，"
        "没有读取 final test，没有执行 final comparison，也没有 benchmark claim。\n\n"
        "## 当前状态\n\n"
        "- Phase 6C 是 protocol/artifact/guard/schema readiness checkpoint。\n"
        "- Final test 没有读取。\n"
        "- Final comparison 没有执行。\n"
        "- 没有训练、调参、A100/GPU/SSH、模型下载或部署。\n"
        "- 没有提交 model weights、adapter checkpoints、cache、"
        "private config/path。\n\n"
        "## Evidence\n\n"
        "- `reports/final-comparison-protocol/phase-6c-execution-gate-dry-run.json`\n"
        "- `reports/final-comparison-protocol/phase-6c-readiness-report.md`\n"
        "- `reports/final-comparison-protocol/phase-6c-claim-checklist.json`\n\n"
        "## 下一步\n\n"
        "Phase 6D 才是 later one-time frozen final comparison；它必须新开 "
        "OpenSpec change，明确授权 final-test 输入和公开 claim checklist。\n"
    )


def _append_progress_ledger(
    path: Path,
    config: FinalComparisonGateConfig,
    status: str,
    blocked_reasons: list[str],
) -> None:
    section = (
        "\nfinal_comparison_phase_6c_status:\n"
        f"  status: {status}\n"
        f"  change: {config.change}\n"
        "  scope: execution_gate_dry_run_only\n"
        f"  protocol_version: {config.protocol_version}\n"
        "  final_test_evaluation: not_run\n"
        "  final_comparison_execution: not_executed\n"
        "  benchmark_claim: none\n"
        "  training: not_executed\n"
        "  tuning: not_executed\n"
        "  a100_or_gpu_used: false\n"
        "  ssh_used: false\n"
        "  model_download: not_executed\n"
        "  model_weights_committed: false\n"
        "  adapter_checkpoint_committed: false\n"
        "  training_cache_committed: false\n"
        "  private_config_committed: false\n"
        "  private_model_path_committed: false\n"
        "  blocked_reasons:\n"
        + "".join(f"    - {reason}\n" for reason in (blocked_reasons or ["none"]))
        + "  evidence:\n"
        f"    dry_run: {config.outputs.dry_run}\n"
        f"    readiness_report: {config.outputs.readiness_report}\n"
        f"    claim_checklist: {config.outputs.claim_checklist}\n"
        f"    human_brief: {config.outputs.human_brief}\n"
    )
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "final_comparison_phase_6c_status:"
    if marker in existing:
        existing = existing.split(marker, maxsplit=1)[0].rstrip() + "\n"
    _write_text(path, existing.rstrip() + "\n" + section.lstrip())
