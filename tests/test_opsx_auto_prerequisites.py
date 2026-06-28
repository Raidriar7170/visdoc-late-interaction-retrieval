"""Tests for the repo-local opsx-auto prerequisite configuration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = REPO_ROOT / ".opsx-auto-config"
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-local-core.sh"


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _sort_scalars(items: Any) -> list[Any]:
    values = items if isinstance(items, list) else []
    return sorted(values, key=_stable_json)


def _sort_evidence_requirements(items: Any) -> list[dict[str, Any]]:
    values = [dict(item) for item in items if isinstance(item, dict)]
    return sorted(values, key=lambda item: str(item.get("requirement_id", "")))


def _sort_goal_definitions(items: Any) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        goal = dict(item)
        goal["evidence_requirements"] = _sort_evidence_requirements(
            goal.get("evidence_requirements", [])
        )
        goal["required_dependency_goal_ids"] = sorted(
            str(value)
            for value in goal.get("required_dependency_goal_ids", [])
            if isinstance(value, str)
        )
        goals.append(goal)
    return sorted(goals, key=lambda item: str(item.get("goal_id", "")))


def _contract_hash(contract: dict[str, Any]) -> str:
    fields = [
        "goal_definitions",
        "constraints",
        "success_thresholds",
        "completion_criteria",
        "privacy_boundaries",
        "release_boundaries",
        "non_goal_statements",
    ]
    payload = {}
    for field in fields:
        if field == "goal_definitions":
            payload[field] = _sort_goal_definitions(contract.get(field, []))
        else:
            payload[field] = _sort_scalars(contract.get(field, []))
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def test_opsx_auto_config_files_exist_and_do_not_initialize_store() -> None:
    for name in (
        "unattended-local.json",
        "contract.json",
        "validation-policy.json",
    ):
        assert (CONFIG_ROOT / name).is_file()
        _load_json(CONFIG_ROOT / name)

    assert not (REPO_ROOT / ".opsx-auto" / "loop-state.json").exists()
    assert not (REPO_ROOT / ".opsx-auto" / "genesis-state.json").exists()
    assert not (REPO_ROOT / ".opsx-auto" / "events.jsonl").exists()


def test_unattended_local_config_uses_bounded_edit_scope() -> None:
    config = _load_json(CONFIG_ROOT / "unattended-local.json")

    assert config["mode"] == "unattended-local-core"
    assert config["phase_file_globs"] == [".opsx-auto-inbox/*.json"]
    assert config["validation_profile"] == "local-core"
    assert config["completion_validation_profile"] == "local-core"

    allowed_paths = config["allowed_paths"]
    assert isinstance(allowed_paths, list)
    assert allowed_paths
    assert "**" not in allowed_paths
    assert all(isinstance(path, str) and path for path in allowed_paths)
    assert all(not path.startswith("/") for path in allowed_paths)
    assert all(".." not in Path(path).parts for path in allowed_paths)

    forbidden_roots = {".git", ".opsx-auto", ".opsx-auto-config"}
    for path in allowed_paths:
        assert Path(path).parts[0] not in forbidden_roots


def test_validation_policy_binds_local_wrapper_and_interpreter_hashes() -> None:
    policy = _load_json(CONFIG_ROOT / "validation-policy.json")
    profile = policy["profiles"]["local-core"]

    assert profile["argv"] == ["scripts/validate-local-core.sh"]
    assert profile["repo_script_sha256"] == _sha256(SCRIPT_PATH)
    assert profile["shebang_interpreter_path"] == "/bin/bash"
    assert profile["shebang_interpreter_realpath"] == str(Path("/bin/bash").resolve())
    assert profile["shebang_interpreter_sha256"] == _sha256(Path("/bin/bash"))
    assert isinstance(profile["timeout_seconds"], int)
    assert 1 <= profile["timeout_seconds"] <= 600

    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert script_text.startswith("#!/bin/bash\n")
    forbidden_fragments = (
        "pip install",
        "curl ",
        "wget ",
        "|",
        "git add",
        "git commit",
        "git merge",
        "git push",
        "openspec archive",
        ".opsx-auto/",
    )
    for fragment in forbidden_fragments:
        assert fragment not in script_text


def test_contract_has_mandatory_evidence_and_self_consistent_hash() -> None:
    contract = _load_json(CONFIG_ROOT / "contract.json")

    assert contract["schema_version"] == 2
    assert contract["loop_id"] == "visdoc-text-baselines-auto"
    assert contract["contract_sha256"] == _contract_hash(contract)

    core_goals = [
        goal for goal in contract["goal_definitions"] if goal["role"] == "core"
    ]
    assert core_goals
    for goal in core_goals:
        requirements = goal["evidence_requirements"]
        assert any(requirement["mandatory"] is True for requirement in requirements)
        assert all(requirement["requirement_id"] for requirement in requirements)
