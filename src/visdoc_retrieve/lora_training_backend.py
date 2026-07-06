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
    def device(self) -> str: ...

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

    if config.backend_dependency == "colpali_engine":
        return _run_colpali_engine_tiny_lora_runner(
            config,
            repo_root=repo_root,
            samples=samples,
            backend_module=backend_module,
        )

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


def _run_colpali_engine_tiny_lora_runner(
    config: BackendConfig,
    *,
    repo_root: Path,
    samples: Sequence[Mapping[str, object]],
    backend_module: Any,
) -> dict[str, object]:
    """Run the reviewed repo-owned ColQwen2 tiny LoRA pilot."""

    sample_count = len(samples)
    model_path = _resolve_path(repo_root, config.local_model_path)
    model, processor, model_load_errors = _load_colpali_components(
        backend_module,
        model_path=model_path,
    )
    if model is None or processor is None:
        return _blocked_backend_result(
            "colpali_model_load_failed",
            "ColQwen2 local model load failed: "
            + "; ".join(model_load_errors),
            sample_count=sample_count,
        )

    try:
        peft = importlib.import_module("peft")
        lora_config = peft.LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            bias="none",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        model = peft.get_peft_model(model, lora_config)
    except Exception as exc:
        return _blocked_backend_result(
            "colpali_lora_wrap_failed",
            f"ColQwen2 LoRA wrapping failed: {exc}",
            sample_count=sample_count,
        )

    query_texts = _query_texts_for_samples(samples, repo_root=repo_root)
    try:
        batch = _process_queries(processor, query_texts)
        batch = _move_batch_to_device(batch, config=config)
    except Exception as exc:
        return _blocked_backend_result(
            "colpali_processor_failed",
            f"ColQwen2 query processing failed: {exc}",
            sample_count=sample_count,
        )

    try:
        if hasattr(model, "to"):
            model = model.to(config.device)
        if hasattr(model, "train"):
            model.train()
        params = _trainable_parameters(model)
        if not params:
            return _blocked_backend_result(
                "colpali_no_trainable_parameters",
                "ColQwen2 LoRA runner found no trainable parameters.",
                sample_count=sample_count,
            )
        torch = importlib.import_module("torch")
        optimizer = torch.optim.AdamW(params, lr=config.learning_rate)
        if hasattr(optimizer, "zero_grad"):
            optimizer.zero_grad()
        output = _call_model(model, batch)
        loss = _scalar_loss_from_output(output)
        loss.backward()
        optimizer.step()
        if hasattr(optimizer, "zero_grad"):
            optimizer.zero_grad()
    except Exception as exc:
        return _blocked_backend_result(
            "colpali_optimizer_step_failed",
            f"ColQwen2 tiny optimizer step failed: {exc}",
            sample_count=sample_count,
        )

    adapter_created = False
    if config.save_adapter:
        adapter_dir = _resolve_path(repo_root, config.adapter_output_dir)
        try:
            adapter_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(str(adapter_dir))
            adapter_created = True
        except Exception as exc:
            return _blocked_backend_result(
                "colpali_adapter_save_failed",
                f"ColQwen2 adapter save failed: {exc}",
                sample_count=sample_count,
            )

    return {
        "status": "pilot_run",
        "training_executed": True,
        "effective_training_sample_count": sample_count,
        "adapter_checkpoint_created": adapter_created,
        "adapter_checkpoint_path": (
            str(config.adapter_output_dir) if adapter_created else None
        ),
        "max_steps": config.max_steps,
        "final_test_used": False,
        "local_files_only": True,
        "benchmark_improvement_claim": False,
        "pilot_loss_reported_as_model_improvement": False,
        "backend": "repo_owned_colpali_engine_tiny_lora_runner",
    }


def _load_colpali_components(
    backend_module: Any,
    *,
    model_path: Path,
) -> tuple[Any | None, Any | None, list[str]]:
    errors: list[str] = []
    try:
        transformers = importlib.import_module("transformers")
        model_cls = getattr(transformers, "ColQwen2ForRetrieval", None)
        processor_cls = getattr(transformers, "ColQwen2Processor", None)
        model_from_pretrained = getattr(model_cls, "from_pretrained", None)
        processor_from_pretrained = getattr(processor_cls, "from_pretrained", None)
        if callable(model_from_pretrained) and callable(processor_from_pretrained):
            try:
                return (
                    model_from_pretrained(str(model_path), local_files_only=True),
                    processor_from_pretrained(str(model_path), local_files_only=True),
                    errors,
                )
            except Exception as exc:
                errors.append(f"transformers ColQwen2ForRetrieval: {exc}")
    except Exception as exc:
        errors.append(f"transformers ColQwen2 unavailable: {exc}")

    try:
        return (
            backend_module.ColQwen2.from_pretrained(
                str(model_path),
                local_files_only=True,
            ),
            backend_module.ColQwen2Processor.from_pretrained(
                str(model_path),
                local_files_only=True,
            ),
            errors,
        )
    except Exception as exc:
        errors.append(f"colpali_engine ColQwen2: {exc}")
    return None, None, errors


def _blocked_backend_result(
    code: str,
    message: str,
    *,
    sample_count: int,
) -> dict[str, object]:
    return {
        "status": "blocked",
        "blocked_code": code,
        "blocked_message": message,
        "training_executed": False,
        "effective_training_sample_count": sample_count,
        "adapter_checkpoint_created": False,
        "adapter_checkpoint_path": None,
        "final_test_used": False,
    }


def _query_texts_for_samples(
    samples: Sequence[Mapping[str, object]],
    *,
    repo_root: Path,
) -> list[str]:
    query_index = _load_query_text_index(
        repo_root / "data/synthetic-smoke/queries.jsonl"
    )
    texts: list[str] = []
    for sample in samples:
        query_id = str(sample.get("query_id", ""))
        texts.append(query_index.get(query_id) or query_id or "visdoc training query")
    return texts


def _load_query_text_index(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    query_index: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            query_id = record.get("query_id")
            query = record.get("query")
            if isinstance(query_id, str) and isinstance(query, str):
                query_index[query_id] = query
    return query_index


def _process_queries(processor: Any, query_texts: list[str]) -> Any:
    try:
        return processor.process_queries(texts=query_texts)
    except TypeError as exc:
        try:
            return processor.process_queries(text=query_texts)
        except TypeError:
            raise exc from None


def _move_batch_to_device(batch: Any, *, config: BackendConfig) -> Any:
    if hasattr(batch, "to"):
        return batch.to(config.device)
    if isinstance(batch, Mapping):
        moved: dict[str, object] = {}
        for key, value in batch.items():
            moved[key] = value.to(config.device) if hasattr(value, "to") else value
        return moved
    return batch


def _trainable_parameters(model: Any) -> list[object]:
    parameters = getattr(model, "parameters", None)
    if not callable(parameters):
        return []
    return [
        param
        for param in parameters()
        if getattr(param, "requires_grad", True)
    ]


def _call_model(model: Any, batch: Any) -> Any:
    if isinstance(batch, Mapping):
        return model(**batch)
    return model(**dict(batch))


def _scalar_loss_from_output(output: Any) -> Any:
    candidates: list[Any] = []
    if isinstance(output, Mapping):
        candidates.extend(
            output.get(key)
            for key in ("loss", "last_hidden_state", "embeddings", "logits")
        )
    elif isinstance(output, (list, tuple)):
        candidates.extend(output)
    else:
        candidates.append(output)

    for candidate in candidates:
        if candidate is None:
            continue
        loss = candidate.float() if hasattr(candidate, "float") else candidate
        loss = loss.mean() if hasattr(loss, "mean") else loss
        if hasattr(loss, "backward"):
            return loss
    raise ValueError("model output did not provide a differentiable scalar loss")


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
