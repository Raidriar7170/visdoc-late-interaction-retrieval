"""Phase 5D guarded local LoRA / QLoRA pilot backend wiring.

This module intentionally has no top-level torch, transformers, peft, or
ColPali imports. Optional ML dependencies are imported only inside
``run_local_lora_pilot`` after the launcher gates have passed.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

MAX_BACKEND_SAMPLE_LIMIT = 8


class BackendConfig(Protocol):
    """Subset of the pilot config consumed by the backend."""

    @property
    def backend_dependency(self) -> str: ...

    @property
    def local_files_only(self) -> bool: ...

    @property
    def local_model_path(self) -> Path: ...

    @property
    def train_hard_negatives_path(self) -> Path: ...

    @property
    def candidate_universe_id(self) -> str: ...

    @property
    def adapter_output_dir(self) -> Path: ...

    @property
    def sample_limit(self) -> int: ...

    @property
    def max_steps(self) -> int: ...

    @property
    def save_adapter(self) -> bool: ...

    @property
    def qlora(self) -> bool: ...

    @property
    def lora_r(self) -> int: ...

    @property
    def lora_alpha(self) -> int: ...

    @property
    def lora_dropout(self) -> float: ...

    @property
    def learning_rate(self) -> float: ...

    @property
    def seed(self) -> int: ...



def load_train_hard_negative_samples(
    path: Path,
    *,
    repo_root: Path,
    sample_limit: int,
    candidate_universe_id: str,
) -> tuple[dict[str, object], ...]:
    """Load a capped train-only hard-negative sample for the tiny pilot."""

    if sample_limit <= 0 or sample_limit > MAX_BACKEND_SAMPLE_LIMIT:
        raise ValueError(f"sample_limit must be <= {MAX_BACKEND_SAMPLE_LIMIT}")
    if _looks_like_final_test_path(path):
        raise ValueError("train hard negatives must not point at final test data")

    resolved = _resolve_path(repo_root, path)
    samples: list[dict[str, object]] = []
    with resolved.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if len(samples) >= sample_limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number} is not valid JSON: {exc.msg}"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must be a JSON object")
            if record.get("split") != "train":
                raise ValueError(
                    f"{path}:{line_number} must be train split, got "
                    f"{record.get('split')!r}"
                )
            if record.get("candidate_universe_id") != candidate_universe_id:
                raise ValueError(
                    f"{path}:{line_number} candidate_universe_id must be "
                    f"{candidate_universe_id!r}"
                )
            samples.append(cast(dict[str, object], dict(record)))
    return tuple(samples)


def run_local_lora_pilot(
    config: BackendConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Run the optional local-only backend or return structured blocked evidence."""

    missing = _missing_optional_dependencies(
        ("torch", "transformers", "peft", config.backend_dependency)
    )
    if missing:
        return {
            "status": "blocked",
            "blocked_code": "optional_training_dependency_missing",
            "blocked_message": (
                "Missing optional real-training dependencies: "
                + ", ".join(missing)
            ),
            "missing_dependencies": missing,
            "training_executed": False,
            "effective_training_sample_count": 0,
            "final_test_used": False,
        }

    if not config.local_files_only:
        return {
            "status": "blocked",
            "blocked_code": "local_files_only_disabled",
            "blocked_message": "local_files_only must remain true.",
            "training_executed": False,
            "effective_training_sample_count": 0,
            "final_test_used": False,
        }

    try:
        samples = load_train_hard_negative_samples(
            config.train_hard_negatives_path,
            repo_root=repo_root,
            sample_limit=config.sample_limit,
            candidate_universe_id=config.candidate_universe_id,
        )
    except ValueError as exc:
        return {
            "status": "blocked",
            "blocked_code": "training_sample_invalid",
            "blocked_message": str(exc),
            "training_executed": False,
            "effective_training_sample_count": 0,
            "final_test_used": False,
        }
    if not samples:
        return {
            "status": "blocked",
            "blocked_code": "training_sample_empty",
            "blocked_message": "No train hard-negative samples were available.",
            "training_executed": False,
            "effective_training_sample_count": 0,
            "final_test_used": False,
        }

    backend_module = importlib.import_module(config.backend_dependency)
    backend_runner = getattr(backend_module, "run_visdoc_lora_pilot", None)
    if callable(backend_runner):
        result = backend_runner(
            config=config,
            repo_root=repo_root,
            train_samples=samples,
        )
        if isinstance(result, dict):
            return _normalize_backend_result(
                result,
                sample_count=len(samples),
                config=config,
            )
        return {
            "status": "blocked",
            "blocked_code": "backend_result_invalid",
            "blocked_message": "Backend runner did not return a mapping.",
            "training_executed": False,
            "effective_training_sample_count": len(samples),
            "final_test_used": False,
        }

    return _run_transformers_peft_wiring_probe(
        config,
        repo_root=repo_root,
        sample_count=len(samples),
    )


def _missing_optional_dependencies(names: Sequence[str]) -> tuple[str, ...]:
    missing: list[str] = []
    for name in names:
        if name in sys.modules:
            continue
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            missing.append(name)
    return tuple(dict.fromkeys(missing))


def _run_transformers_peft_wiring_probe(
    config: BackendConfig,
    *,
    repo_root: Path,
    sample_count: int,
) -> dict[str, object]:
    transformers = importlib.import_module("transformers")
    peft = importlib.import_module("peft")

    auto_model = getattr(transformers, "AutoModel", None)
    from_pretrained = getattr(auto_model, "from_pretrained", None)
    lora_config_cls = getattr(peft, "LoraConfig", None)
    if not callable(from_pretrained) or not callable(lora_config_cls):
        return {
            "status": "blocked",
            "blocked_code": "backend_api_unavailable",
            "blocked_message": (
                "transformers/peft APIs needed for local backend wiring are "
                "not available."
            ),
            "training_executed": False,
            "effective_training_sample_count": sample_count,
            "final_test_used": False,
        }

    return {
        "status": "blocked",
        "blocked_code": "backend_training_step_unavailable",
        "blocked_message": (
            "Optional dependencies are importable, but no reviewed backend "
            "runner performed a tiny optimizer-backed training step."
        ),
        "training_executed": False,
        "effective_training_sample_count": sample_count,
        "adapter_checkpoint_created": False,
        "adapter_checkpoint_path": None,
        "max_steps": config.max_steps,
        "final_test_used": False,
        "local_files_only": True,
        "backend": "transformers_peft_wiring_probe",
    }


def _normalize_backend_result(
    result: Mapping[str, Any],
    *,
    sample_count: int,
    config: BackendConfig,
) -> dict[str, object]:
    normalized = dict(result)
    normalized.setdefault("training_executed", normalized.get("status") == "pilot_run")
    normalized.setdefault("effective_training_sample_count", sample_count)
    normalized.setdefault("adapter_checkpoint_created", False)
    normalized.setdefault("adapter_checkpoint_path", None)
    normalized.setdefault("max_steps", config.max_steps)
    normalized.setdefault("final_test_used", False)
    return normalized


def _looks_like_final_test_path(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts.intersection({"test", "final-test", "final_test"}):
        return True
    lowered_name = path.name.lower()
    return lowered_name in {"test.jsonl", "final-test.jsonl", "final_test.jsonl"}


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path
