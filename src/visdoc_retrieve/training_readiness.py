"""Phase 5A training-readiness dry-run helpers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from visdoc_retrieve.data_schema import (
    PageRecord,
    QueryRecord,
    ValidationError,
    load_jsonl,
    validate_pages,
    validate_queries,
)
from visdoc_retrieve.hard_negatives import (
    HardNegativeRecord,
    load_hard_negative_jsonl,
    validate_hard_negative_leakage,
)


class TrainingReadinessConfigError(ValueError):
    """Raised when a Phase 5A dry-run config is invalid."""


class TrainingReadinessDatasetError(ValidationError):
    """Raised when Phase 5A input artifacts violate readiness boundaries."""


@dataclass(frozen=True, slots=True)
class TrainingReadinessOutputs:
    """Report output paths for the dry-run trainer."""

    artifact_freeze: Path
    dataset_summary: Path
    dry_run_card: Path
    safety_check: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class TrainingReadinessConfig:
    """Parsed Phase 5A dry-run config."""

    base_model_name_or_path: str
    model_revision: str
    local_model_path: Path
    adapter_output_dir: Path
    train_hard_negatives_path: Path
    dev_hard_negatives_path: Path
    corpus_path: Path
    queries_path: Path
    qrels_path: Path
    candidate_universe_id: str
    loss_type: str
    batch_size: int
    gradient_accumulation_steps: int
    max_steps: int
    learning_rate: float
    seed: int
    device: str
    dry_run: bool
    allow_final_test: bool
    dry_run_sample_limit: int
    report_timestamp_utc: str
    outputs: TrainingReadinessOutputs
    config_path: Path | None


@dataclass(frozen=True, slots=True)
class TrainingTriple:
    """One query, positive page, negative page training-readiness triple."""

    query_id: str
    positive_page_id: str
    negative_page_id: str
    split: str
    candidate_universe_id: str
    negative_source: str
    rank: int


@dataclass(frozen=True, slots=True)
class TrainingTripleDataset:
    """Loaded train/dev readiness triples."""

    train: tuple[TrainingTriple, ...]
    dev: tuple[TrainingTriple, ...]


@dataclass(frozen=True, slots=True)
class MockBatch:
    """CPU-safe mock ranking batch."""

    query_ids: tuple[str, ...]
    positive_page_ids: tuple[str, ...]
    negative_page_ids: tuple[str, ...]
    positive_scores: tuple[float, ...]
    negative_scores: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class MockLossResult:
    """Pairwise mock loss result."""

    loss: float
    item_count: int
    empty: bool


def load_training_readiness_config(path: Path) -> TrainingReadinessConfig:
    """Load and validate a Phase 5A dry-run JSON config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TrainingReadinessConfigError(
            "training-readiness config must be an object"
        )

    outputs = _required_mapping(data, "outputs")
    config = TrainingReadinessConfig(
        base_model_name_or_path=_required_str(data, "base_model_name_or_path"),
        model_revision=_required_str(data, "model_revision"),
        local_model_path=Path(_required_str(data, "local_model_path")),
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
        batch_size=_positive_int(data, "batch_size"),
        gradient_accumulation_steps=_positive_int(
            data,
            "gradient_accumulation_steps",
        ),
        max_steps=_positive_int(data, "max_steps"),
        learning_rate=_positive_float(data, "learning_rate"),
        seed=_positive_int(data, "seed"),
        device=_required_str(data, "device"),
        dry_run=_required_bool(data, "dry_run"),
        allow_final_test=_required_bool(data, "allow_final_test"),
        dry_run_sample_limit=_positive_int(data, "dry_run_sample_limit"),
        report_timestamp_utc=_required_str(data, "report_timestamp_utc"),
        outputs=TrainingReadinessOutputs(
            artifact_freeze=Path(_required_str(outputs, "artifact_freeze")),
            dataset_summary=Path(_required_str(outputs, "dataset_summary")),
            dry_run_card=Path(_required_str(outputs, "dry_run_card")),
            safety_check=Path(_required_str(outputs, "safety_check")),
            human_brief=Path(_required_str(outputs, "human_brief")),
            progress_ledger=Path(_required_str(outputs, "progress_ledger")),
        ),
        config_path=path,
    )
    if config.allow_final_test:
        raise TrainingReadinessConfigError("allow_final_test must remain false")
    if not config.dry_run:
        raise TrainingReadinessConfigError("dry_run must remain true")
    if config.loss_type != "mock_pairwise_margin":
        raise TrainingReadinessConfigError("loss_type must be mock_pairwise_margin")
    if config.device != "cpu":
        raise TrainingReadinessConfigError("device must be cpu for Phase 5A")
    return config


def check_training_readiness_paths(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
) -> None:
    """Validate required input paths without loading models or writing checkpoints."""

    for field_name, path in {
        "train_hard_negatives_path": config.train_hard_negatives_path,
        "dev_hard_negatives_path": config.dev_hard_negatives_path,
        "corpus_path": config.corpus_path,
        "queries_path": config.queries_path,
        "qrels_path": config.qrels_path,
    }.items():
        resolved = _resolve_path(repo_root, path)
        if not resolved.is_file():
            raise TrainingReadinessConfigError(f"{field_name} does not exist: {path}")


def load_training_triples(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
    dry_run_sample_limit: int | None = None,
) -> TrainingTripleDataset:
    """Load and validate train/dev hard-negative triples."""

    check_training_readiness_paths(config, repo_root=repo_root)
    pages = validate_pages(load_jsonl(_resolve_path(repo_root, config.corpus_path)))
    queries = validate_queries(
        load_jsonl(_resolve_path(repo_root, config.queries_path)),
        pages,
    )
    _validate_qrels(config, repo_root=repo_root, pages=pages, queries=queries)

    train_records = _load_split_records(
        _resolve_path(repo_root, config.train_hard_negatives_path),
        expected_split="train",
        candidate_universe_id=config.candidate_universe_id,
        pages=pages,
        queries=queries,
    )
    dev_records = _load_split_records(
        _resolve_path(repo_root, config.dev_hard_negatives_path),
        expected_split="dev",
        candidate_universe_id=config.candidate_universe_id,
        pages=pages,
        queries=queries,
    )

    train = tuple(_triple_from_record(record) for record in train_records)
    dev = tuple(_triple_from_record(record) for record in dev_records)
    if dry_run_sample_limit is not None:
        train = train[:dry_run_sample_limit]
        dev = dev[:dry_run_sample_limit]
    return TrainingTripleDataset(train=train, dev=dev)


def build_mock_batch(
    triples: Sequence[TrainingTriple],
    *,
    seed: int,
    batch_size: int,
) -> MockBatch:
    """Build a deterministic mock scoring batch from triples."""

    selected = tuple(triples[:batch_size])
    return MockBatch(
        query_ids=tuple(triple.query_id for triple in selected),
        positive_page_ids=tuple(triple.positive_page_id for triple in selected),
        negative_page_ids=tuple(triple.negative_page_id for triple in selected),
        positive_scores=tuple(
            _fake_score(triple.query_id, triple.positive_page_id, seed, offset=0.6)
            for triple in selected
        ),
        negative_scores=tuple(
            _fake_score(triple.query_id, triple.negative_page_id, seed, offset=0.0)
            for triple in selected
        ),
    )


def mock_pairwise_ranking_loss(
    *,
    positive_scores: Sequence[float],
    negative_scores: Sequence[float],
    margin: float = 1.0,
) -> MockLossResult:
    """Compute a simple pairwise margin loss without ML libraries."""

    if len(positive_scores) != len(negative_scores):
        raise TrainingReadinessDatasetError("mock score shape mismatch")
    if not positive_scores:
        return MockLossResult(loss=0.0, item_count=0, empty=True)
    losses = [
        max(0.0, margin - (positive - negative))
        for positive, negative in zip(positive_scores, negative_scores, strict=True)
    ]
    return MockLossResult(
        loss=sum(losses) / len(losses),
        item_count=len(losses),
        empty=False,
    )


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for a local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_training_readiness_dry_run(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Run the Phase 5A dry-run and write readiness evidence artifacts."""

    full_dataset = load_training_triples(config, repo_root=repo_root)
    sample_dataset = load_training_triples(
        config,
        repo_root=repo_root,
        dry_run_sample_limit=config.dry_run_sample_limit,
    )
    mock_batch = build_mock_batch(
        sample_dataset.train,
        seed=config.seed,
        batch_size=config.batch_size,
    )
    loss = mock_pairwise_ranking_loss(
        positive_scores=mock_batch.positive_scores,
        negative_scores=mock_batch.negative_scores,
    )

    freeze = _artifact_freeze(config, repo_root=repo_root)
    summary = _dataset_summary(
        config,
        full_dataset=full_dataset,
        mock_batch=mock_batch,
        loss=loss,
    )
    safety = safety_check(config, repo_root=repo_root)
    outputs = _resolved_outputs(config.outputs, repo_root=repo_root)
    _write_json(outputs.artifact_freeze, freeze)
    _write_json(outputs.dataset_summary, summary)
    _write_json(outputs.safety_check, safety)
    _write_dry_run_card(outputs.dry_run_card, freeze=freeze, summary=summary)
    _write_human_brief(outputs.human_brief, freeze=freeze, summary=summary)
    _update_progress_ledger(outputs.progress_ledger, summary)
    return {
        "status": "training_readiness_dry_run_generated",
        "artifact_freeze": str(outputs.artifact_freeze),
        "dataset_summary": str(outputs.dataset_summary),
        "safety_check": str(outputs.safety_check),
        "dry_run_card": str(outputs.dry_run_card),
        "human_brief": str(outputs.human_brief),
        "progress_ledger": str(outputs.progress_ledger),
    }


def safety_check(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Return explicit Phase 5A safety checks derived from local artifacts."""

    forbidden_scan = _forbidden_artifact_scan(config, repo_root=repo_root)
    model_weight_paths = cast(
        Sequence[str],
        forbidden_scan["model_weight_paths"],
    )
    adapter_checkpoint_paths = cast(
        Sequence[str],
        forbidden_scan["adapter_checkpoint_paths"],
    )
    embedding_cache_paths = cast(
        Sequence[str],
        forbidden_scan["embedding_cache_paths"],
    )
    return {
        "final_test_not_used": True,
        "training_not_executed": True,
        "model_download_not_executed": True,
        "gpu_not_required": True,
        "model_weights_committed": bool(model_weight_paths),
        "adapter_checkpoint_committed": bool(adapter_checkpoint_paths),
        "embedding_cache_committed": bool(embedding_cache_paths),
        "benchmark_claim_added": False,
        "mock_dry_run_results_are_model_performance": False,
        "forbidden_artifact_scan": forbidden_scan,
    }


def _forbidden_artifact_scan(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    model_weight_suffixes = {".bin", ".ckpt", ".pt", ".pth", ".safetensors"}
    model_weight_paths = [
        _repo_relative(repo_root, path)
        for path in _iter_repo_files(repo_root)
        if path.suffix.lower() in model_weight_suffixes
    ]

    adapter_dir = _resolve_path(repo_root, config.adapter_output_dir)
    adapter_checkpoint_paths = [
        _repo_relative(repo_root, path)
        for path in _iter_files(adapter_dir)
    ]

    phase5a_dirs = {
        _resolve_path(repo_root, output_path).parent
        for output_path in (
            config.outputs.artifact_freeze,
            config.outputs.dataset_summary,
            config.outputs.dry_run_card,
            config.outputs.safety_check,
            config.outputs.human_brief,
        )
    }
    phase5a_dirs.add(adapter_dir)
    embedding_cache_paths = sorted(
        {
            _repo_relative(repo_root, path)
            for directory in phase5a_dirs
            for path in _iter_files(directory)
            if _looks_like_embedding_cache(path)
        }
    )

    return {
        "model_weight_paths": sorted(model_weight_paths),
        "adapter_checkpoint_paths": sorted(adapter_checkpoint_paths),
        "embedding_cache_paths": embedding_cache_paths,
    }


def _iter_repo_files(repo_root: Path) -> tuple[Path, ...]:
    excluded_parts = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".worktrees",
        "__pycache__",
    }
    paths: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(repo_root).parts
        except ValueError:
            continue
        if any(part in excluded_parts for part in relative_parts):
            continue
        paths.append(path)
    return tuple(sorted(paths))


def _iter_files(directory: Path) -> tuple[Path, ...]:
    if not directory.exists():
        return ()
    return tuple(sorted(path for path in directory.rglob("*") if path.is_file()))


def _looks_like_embedding_cache(path: Path) -> bool:
    name = path.name.lower()
    if path.suffix.lower() in {".faiss", ".npy", ".npz"}:
        return True
    return "embedding" in name or "cache" in name


def _repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _load_split_records(
    path: Path,
    *,
    expected_split: str,
    candidate_universe_id: str,
    pages: Sequence[PageRecord],
    queries: Sequence[QueryRecord],
) -> tuple[HardNegativeRecord, ...]:
    records = load_hard_negative_jsonl(path)
    for record in records:
        if record.split != expected_split:
            raise TrainingReadinessDatasetError(
                f"{expected_split} hard-negative file contains {record.split} split"
            )
        if record.candidate_universe_id != candidate_universe_id:
            raise TrainingReadinessDatasetError(
                "candidate_universe_id does not match training-readiness config"
            )
    try:
        validate_hard_negative_leakage(
            records,
            pages=pages,
            queries=queries,
            final_test_split="test",
        )
    except ValidationError as exc:
        raise TrainingReadinessDatasetError(str(exc)) from exc
    return records


def _validate_qrels(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
    pages: Sequence[PageRecord],
    queries: Sequence[QueryRecord],
) -> None:
    qrels = validate_queries(
        load_jsonl(_resolve_path(repo_root, config.qrels_path)),
        pages,
    )
    expected = {
        query.query_id: tuple(query.positive_page_ids)
        for query in queries
        if query.split in {"train", "dev"}
    }
    actual = {
        query.query_id: tuple(query.positive_page_ids)
        for query in qrels
        if query.split in {"train", "dev"}
    }
    if expected != actual:
        raise TrainingReadinessDatasetError("qrels positive pages do not match queries")


def _triple_from_record(record: HardNegativeRecord) -> TrainingTriple:
    return TrainingTriple(
        query_id=record.query_id,
        positive_page_id=record.positive_page_id,
        negative_page_id=record.negative_page_id,
        split=record.split,
        candidate_universe_id=record.candidate_universe_id,
        negative_source=record.negative_source,
        rank=record.rank,
    )


def _fake_score(query_id: str, page_id: str, seed: int, *, offset: float) -> float:
    raw = hashlib.sha256(f"{seed}:{query_id}:{page_id}".encode()).digest()
    integer = int.from_bytes(raw[:8], "big")
    return round(offset + (integer % 10000) / 10000.0, 6)


def _artifact_freeze(
    config: TrainingReadinessConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    artifacts = {
        "train_hard_negatives": config.train_hard_negatives_path,
        "dev_hard_negatives": config.dev_hard_negatives_path,
        "corpus": config.corpus_path,
        "queries": config.queries_path,
        "qrels": config.qrels_path,
    }
    return {
        "schema": "training_readiness_artifact_freeze/v1",
        "timestamp_utc": config.report_timestamp_utc,
        "candidate_universe_id": config.candidate_universe_id,
        "split_policy": {
            "train": "train hard negatives only",
            "dev": "dev hard negatives only",
            "final_test": "excluded",
        },
        "metric_definitions_ref": (
            "openspec/specs/retrieval-evaluation-metrics/spec.md"
        ),
        "model_revision": config.model_revision,
        "base_model_name_or_path": config.base_model_name_or_path,
        "local_model_path": str(config.local_model_path),
        "final_test_used": False,
        "statement": (
            "Phase 5A freezes inputs for a future dry-run/training handoff; "
            "final test data is not used."
        ),
        "artifacts": {
            name: {
                "path": str(path),
                "sha256": sha256_file(_resolve_path(repo_root, path)),
            }
            for name, path in artifacts.items()
        },
    }


def _dataset_summary(
    config: TrainingReadinessConfig,
    *,
    full_dataset: TrainingTripleDataset,
    mock_batch: MockBatch,
    loss: MockLossResult,
) -> dict[str, object]:
    return {
        "schema": "training_readiness_dataset_summary/v1",
        "status": "dry_run_generated",
        "candidate_universe_id": config.candidate_universe_id,
        "train": _split_summary(full_dataset.train),
        "dev": _split_summary(full_dataset.dev),
        "mock_batch": {
            "batch_size": len(mock_batch.query_ids),
            "query_ids": list(mock_batch.query_ids),
            "positive_scores": list(mock_batch.positive_scores),
            "negative_scores": list(mock_batch.negative_scores),
            "loss": {
                "loss": loss.loss,
                "item_count": loss.item_count,
                "empty": loss.empty,
                "not_model_performance": True,
            },
        },
        "dry_run": True,
        "training_executed": False,
        "final_test_evaluation": "not_run",
        "benchmark_claim": "none",
    }


def _split_summary(triples: Sequence[TrainingTriple]) -> dict[str, object]:
    sources = Counter(triple.negative_source for triple in triples)
    query_ids = {triple.query_id for triple in triples}
    positive_page_ids = {triple.positive_page_id for triple in triples}
    negative_page_ids = {triple.negative_page_id for triple in triples}
    return {
        "triple_count": len(triples),
        "query_count": len(query_ids),
        "positive_page_count": len(positive_page_ids),
        "negative_page_count": len(negative_page_ids),
        "negative_source_counts": dict(sorted(sources.items())),
    }


def _write_dry_run_card(
    path: Path,
    *,
    freeze: Mapping[str, object],
    summary: Mapping[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    train = cast(Mapping[str, object], summary["train"])
    dev = cast(Mapping[str, object], summary["dev"])
    path.write_text(
        "\n".join(
            [
                "# Phase 5A Training Readiness Dry Run",
                "",
                "Status: dry_run_generated",
                "",
                f"Timestamp: {freeze['timestamp_utc']}",
                f"Candidate universe: {freeze['candidate_universe_id']}",
                f"Train triples: {train['triple_count']}",
                f"Dev triples: {dev['triple_count']}",
                "",
                "Boundary: no training, no model download, no GPU, no adapter "
                "checkpoint, no final test evaluation.",
                "",
                "Mock loss is not model performance and must not be used as a "
                "benchmark or improvement claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_human_brief(
    path: Path,
    *,
    freeze: Mapping[str, object],
    summary: Mapping[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    train = cast(Mapping[str, object], summary["train"])
    dev = cast(Mapping[str, object], summary["dev"])
    path.write_text(
        "\n".join(
            [
                "# Phase 5A 训练就绪简报",
                "",
                "## 一句话结论",
                "Phase 5A 已生成本地 dry-run 训练就绪证据，但不训练、"
                "不下载模型、不使用 GPU、不评估 final test，也不声明性能提升。",
                "",
                "## 当前状态",
                "状态：dry_run_generated，需要主线程 review 后再决定是否进入 "
                "Phase 5B。",
                "",
                "## 本阶段变化",
                f"- 冻结候选集合：{freeze['candidate_universe_id']}",
                f"- 训练三元组：{train['triple_count']}",
                f"- 开发三元组：{dev['triple_count']}",
                "- mock batch 与 mock ranking loss 只验证接口和安全边界。",
                "",
                "## 关键证据",
                "- `reports/training-readiness/artifact-freeze.json`",
                "- `reports/training-readiness/dataset-summary.json`",
                "- `reports/training-readiness/safety-check.json`",
                "- `reports/training-readiness/dry-run-card.md`",
                "",
                "## 不应夸大的结论",
                "这里没有真实 LoRA/QLoRA 训练、没有 adapter checkpoint、"
                "没有 final test 指标、没有 benchmark 或模型优越性声明。",
                "",
                "## 推荐下一步",
                "Phase 5B 如需真实训练，应先通过新的 OpenSpec change 明确模型、"
                "硬件、数据边界、评估标准和公开声明范围。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _update_progress_ledger(path: Path, summary: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    train = cast(Mapping[str, object], summary["train"])
    dev = cast(Mapping[str, object], summary["dev"])
    entry = "\n".join(
        [
            "training_readiness_status:",
            "  status: dry_run_generated",
            "  change: add-training-readiness-phase-5a",
            "  command: PYTHONPATH=src python -m "
            "visdoc_retrieve.train_lora_dry_run --config "
            "configs/train_lora_dry_run.json",
            "  config: configs/train_lora_dry_run.json",
            "  candidate_universe: evaluated_split_pages",
            f"  train_triples: {train['triple_count']}",
            f"  dev_triples: {dev['triple_count']}",
            "  dry_run: true",
            "  training: not_executed",
            "  model_download: not_executed",
            "  gpu_required: false",
            "  adapter_checkpoint: not_created",
            "  final_test_evaluation: not_run",
            "  benchmark_claim: none",
            "  mock_results_are_model_performance: false",
            "  evidence:",
            "    artifact_freeze: reports/training-readiness/artifact-freeze.json",
            "    dataset_summary: reports/training-readiness/dataset-summary.json",
            "    safety_check: reports/training-readiness/safety-check.json",
            "    dry_run_card: reports/training-readiness/dry-run-card.md",
            "    human_brief: docs/human-briefs/2026-07-01-training-readiness.md",
            "",
        ]
    )
    path.write_text(
        _replace_top_level_yaml_section(
            existing,
            section="training_readiness_status",
            replacement=entry,
        ),
        encoding="utf-8",
    )


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


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolved_outputs(
    outputs: TrainingReadinessOutputs,
    *,
    repo_root: Path,
) -> TrainingReadinessOutputs:
    return TrainingReadinessOutputs(
        artifact_freeze=_resolve_path(repo_root, outputs.artifact_freeze),
        dataset_summary=_resolve_path(repo_root, outputs.dataset_summary),
        dry_run_card=_resolve_path(repo_root, outputs.dry_run_card),
        safety_check=_resolve_path(repo_root, outputs.safety_check),
        human_brief=_resolve_path(repo_root, outputs.human_brief),
        progress_ledger=_resolve_path(repo_root, outputs.progress_ledger),
    )


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _required_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise TrainingReadinessConfigError(f"{key} must be an object")
    return value


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TrainingReadinessConfigError(f"{key} must be a non-empty string")
    return value


def _required_bool(data: Mapping[str, object], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise TrainingReadinessConfigError(f"{key} must be a boolean")
    return value


def _positive_int(data: Mapping[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise TrainingReadinessConfigError(f"{key} must be a positive integer")
    return value


def _positive_float(data: Mapping[str, object], key: str) -> float:
    value = data.get(key)
    if (
        not isinstance(value, int | float)
        or isinstance(value, bool)
        or float(value) <= 0.0
    ):
        raise TrainingReadinessConfigError(f"{key} must be a positive number")
    return float(value)
