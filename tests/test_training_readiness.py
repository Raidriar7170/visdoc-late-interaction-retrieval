"""Tests for Phase 5A training-readiness dry-run scaffolding."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from visdoc_retrieve.data_schema import load_jsonl
from visdoc_retrieve.mvp_pipeline import load_mvp_config, run_mvp_pipeline


def test_dry_run_config_parses_and_rejects_unsafe_flags(tmp_path: Path) -> None:
    readiness = _readiness_module()

    config = readiness.load_training_readiness_config(
        Path("configs/train_lora_dry_run.json")
    )

    assert config.base_model_name_or_path == "local-colpali-or-colqwen-placeholder"
    assert config.model_revision == "phase-5a-placeholder"
    assert config.local_model_path == Path("local-models/colpali-or-colqwen")
    assert config.adapter_output_dir == Path(".local/training-readiness/adapters")
    assert config.train_hard_negatives_path == Path(
        "data/derived/hard_negatives/train.jsonl"
    )
    assert config.dev_hard_negatives_path == Path(
        "data/derived/hard_negatives/dev.jsonl"
    )
    assert config.corpus_path == Path("data/synthetic-smoke/pages.jsonl")
    assert config.queries_path == Path("data/synthetic-smoke/queries.jsonl")
    assert config.qrels_path == Path("data/synthetic-smoke/queries.jsonl")
    assert config.candidate_universe_id == "evaluated_split_pages"
    assert config.loss_type == "mock_pairwise_margin"
    assert config.batch_size == 8
    assert config.gradient_accumulation_steps == 1
    assert config.max_steps == 1
    assert config.learning_rate == pytest.approx(0.0001)
    assert config.seed == 17
    assert config.device == "cpu"
    assert config.dry_run is True
    assert config.allow_final_test is False

    unsafe_final = _write_training_config(tmp_path, allow_final_test=True)
    with pytest.raises(
        readiness.TrainingReadinessConfigError,
        match="allow_final_test",
    ):
        readiness.load_training_readiness_config(unsafe_final)

    unsafe_training = _write_training_config(tmp_path, dry_run=False)
    with pytest.raises(readiness.TrainingReadinessConfigError, match="dry_run"):
        readiness.load_training_readiness_config(unsafe_training)

    missing_required = json.loads(unsafe_training.read_text(encoding="utf-8"))
    missing_required.pop("base_model_name_or_path")
    unsafe_training.write_text(
        json.dumps(missing_required, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(readiness.TrainingReadinessConfigError, match="base_model"):
        readiness.load_training_readiness_config(unsafe_training)


def test_hard_negative_triples_validate_boundaries_and_sample_deterministically(
    tmp_path: Path,
) -> None:
    readiness = _readiness_module()
    config = readiness.load_training_readiness_config(
        Path("configs/train_lora_dry_run.json")
    )

    dataset = readiness.load_training_triples(config, repo_root=Path.cwd())
    sampled = readiness.load_training_triples(
        config,
        repo_root=Path.cwd(),
        dry_run_sample_limit=3,
    )

    assert len(dataset.train) == 429
    assert len(dataset.dev) == 429
    assert [triple.query_id for triple in sampled.train] == [
        "manual-a-p01-q01",
        "manual-a-p01-q01",
        "manual-a-p01-q01",
    ]
    assert [triple.negative_page_id for triple in sampled.train] == [
        "manual-a-p04",
        "manual-a-p05",
        "manual-a-p02",
    ]
    assert [triple.query_id for triple in sampled.dev] == [
        "manual-b-p01-q01",
        "manual-b-p01-q01",
        "manual-b-p01-q01",
    ]

    assert readiness.sha256_file(Path("data/derived/hard_negatives/train.jsonl")) == (
        readiness.sha256_file(Path("data/derived/hard_negatives/train.jsonl"))
    )

    leaked_train = tmp_path / "leaked-train.jsonl"
    leaked_record = load_jsonl(Path("data/derived/hard_negatives/train.jsonl"))[0]
    leaked_record["query_id"] = "manual-b-p01-q01"
    leaked_record["positive_page_id"] = "manual-b-p01"
    leaked_record["negative_page_id"] = "manual-b-p04"
    leaked_record["split"] = "dev"
    _write_jsonl(leaked_train, [leaked_record])
    leaked_config = _write_training_config(
        tmp_path,
        train_hard_negatives_path=leaked_train,
    )
    with pytest.raises(readiness.TrainingReadinessDatasetError, match="train.*split"):
        readiness.load_training_triples(
            readiness.load_training_readiness_config(leaked_config),
            repo_root=Path.cwd(),
        )

    cross_split_query = tmp_path / "cross-split-query.jsonl"
    cross_split_record = load_jsonl(Path("data/derived/hard_negatives/train.jsonl"))[0]
    cross_split_record["query_id"] = "manual-b-p01-q01"
    cross_split_record["positive_page_id"] = "manual-b-p01"
    cross_split_record["negative_page_id"] = "manual-b-p04"
    cross_split_record["split"] = "train"
    _write_jsonl(cross_split_query, [cross_split_record])
    cross_split_config = _write_training_config(
        tmp_path,
        train_hard_negatives_path=cross_split_query,
    )
    with pytest.raises(readiness.TrainingReadinessDatasetError, match="query split"):
        readiness.load_training_triples(
            readiness.load_training_readiness_config(cross_split_config),
            repo_root=Path.cwd(),
        )

    final_test_negative = tmp_path / "final-test-negative.jsonl"
    final_test_record = load_jsonl(Path("data/derived/hard_negatives/train.jsonl"))[0]
    final_test_record["negative_page_id"] = "manual-c-p04"
    final_test_record["split"] = "train"
    _write_jsonl(final_test_negative, [final_test_record])
    final_test_config = _write_training_config(
        tmp_path,
        train_hard_negatives_path=final_test_negative,
    )
    with pytest.raises(readiness.TrainingReadinessDatasetError, match="final test"):
        readiness.load_training_triples(
            readiness.load_training_readiness_config(final_test_config),
            repo_root=Path.cwd(),
        )

    mismatched = tmp_path / "mismatched.jsonl"
    mismatched_record = load_jsonl(Path("data/derived/hard_negatives/train.jsonl"))[0]
    mismatched_record["candidate_universe_id"] = "all_pages"
    _write_jsonl(mismatched, [mismatched_record])
    mismatch_config = _write_training_config(
        tmp_path,
        train_hard_negatives_path=mismatched,
    )
    with pytest.raises(readiness.TrainingReadinessDatasetError, match="candidate"):
        readiness.load_training_triples(
            readiness.load_training_readiness_config(mismatch_config),
            repo_root=Path.cwd(),
        )

    collision = tmp_path / "collision.jsonl"
    collision_record = load_jsonl(Path("data/derived/hard_negatives/train.jsonl"))[0]
    collision_record["negative_page_id"] = collision_record["positive_page_id"]
    _write_jsonl(collision, [collision_record])
    collision_config = _write_training_config(
        tmp_path,
        train_hard_negatives_path=collision,
    )
    with pytest.raises(readiness.TrainingReadinessDatasetError, match="positive"):
        readiness.load_training_triples(
            readiness.load_training_readiness_config(collision_config),
            repo_root=Path.cwd(),
        )


def test_mock_batch_and_ranking_loss_are_cpu_safe() -> None:
    readiness = _readiness_module()
    config = readiness.load_training_readiness_config(
        Path("configs/train_lora_dry_run.json")
    )
    dataset = readiness.load_training_triples(
        config,
        repo_root=Path.cwd(),
        dry_run_sample_limit=4,
    )

    batch = readiness.build_mock_batch(dataset.train, seed=config.seed, batch_size=4)

    assert len(batch.query_ids) == 4
    assert len(batch.positive_scores) == 4
    assert len(batch.negative_scores) == 4
    assert batch.positive_scores == readiness.build_mock_batch(
        dataset.train,
        seed=config.seed,
        batch_size=4,
    ).positive_scores

    better = readiness.mock_pairwise_ranking_loss(
        positive_scores=[3.0, 2.5],
        negative_scores=[1.0, 1.5],
    )
    worse = readiness.mock_pairwise_ranking_loss(
        positive_scores=[1.0, 1.5],
        negative_scores=[3.0, 2.5],
    )
    empty = readiness.mock_pairwise_ranking_loss(
        positive_scores=[],
        negative_scores=[],
    )

    assert better.loss < worse.loss
    assert better.item_count == 2
    assert empty.loss == 0.0
    assert empty.item_count == 0
    assert empty.empty is True

    with pytest.raises(readiness.TrainingReadinessDatasetError, match="shape"):
        readiness.mock_pairwise_ranking_loss(
            positive_scores=[1.0],
            negative_scores=[1.0, 2.0],
        )

    assert "torch" not in sys.modules


def test_dry_run_cli_writes_reports_and_project_evidence(tmp_path: Path) -> None:
    readiness = _readiness_module()
    config_path = _write_training_config(tmp_path)
    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    ledger_path = Path(config_data["outputs"]["progress_ledger"])
    ledger_path.write_text(
        "\n".join(
            [
                "current_phase: 4",
                "training_readiness_status:",
                "  status: stale",
                "hard_negative_mining_status:",
                "  status: generated",
                "  training: not_started",
                "  final_test_evaluation: not_run",
                "  benchmark_claim: none",
                "",
            ]
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.train_lora_dry_run",
            "--config",
            str(config_path),
        ],
        cwd=Path.cwd(),
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    report_dir = tmp_path / "reports"
    freeze = json.loads((report_dir / "artifact-freeze.json").read_text())
    summary = json.loads((report_dir / "dataset-summary.json").read_text())
    safety = json.loads((report_dir / "safety-check.json").read_text())
    card = (report_dir / "dry-run-card.md").read_text(encoding="utf-8")
    brief = (tmp_path / "human-brief.md").read_text(encoding="utf-8")
    ledger = yaml.safe_load((tmp_path / "progress-ledger.yaml").read_text())

    assert freeze["candidate_universe_id"] == "evaluated_split_pages"
    assert freeze["model_revision"] == "phase-5a-placeholder"
    assert freeze["final_test_used"] is False
    assert freeze["artifacts"]["train_hard_negatives"]["sha256"] == (
        readiness.sha256_file(Path("data/derived/hard_negatives/train.jsonl"))
    )
    assert freeze["artifacts"]["corpus"]["path"] == "data/synthetic-smoke/pages.jsonl"
    assert "retrieval-evaluation-metrics" in freeze["metric_definitions_ref"]

    assert summary["train"]["triple_count"] == 429
    assert summary["dev"]["triple_count"] == 429
    assert summary["mock_batch"]["loss"]["item_count"] == 8
    assert summary["mock_batch"]["loss"]["not_model_performance"] is True

    assert safety == {
        "final_test_not_used": True,
        "training_not_executed": True,
        "model_download_not_executed": True,
        "gpu_not_required": True,
        "model_weights_committed": False,
        "adapter_checkpoint_committed": False,
        "embedding_cache_committed": False,
        "benchmark_claim_added": False,
        "mock_dry_run_results_are_model_performance": False,
        "forbidden_artifact_scan": {
            "model_weight_paths": [],
            "adapter_checkpoint_paths": [],
            "embedding_cache_paths": [],
        },
    }
    assert "not model performance" in card
    assert "不训练" in brief
    assert ledger["training_readiness_status"]["status"] == "dry_run_generated"
    assert ledger["training_readiness_status"]["final_test_evaluation"] == "not_run"
    assert ledger["training_readiness_status"]["benchmark_claim"] == "none"
    assert ledger["hard_negative_mining_status"]["status"] == "generated"
    assert ledger["hard_negative_mining_status"]["final_test_evaluation"] == "not_run"


def test_existing_cli_surfaces_and_visual_import_safety_hold(tmp_path: Path) -> None:
    from visdoc_retrieve.mine_hard_negatives import main as mine_main

    mvp_report = run_mvp_pipeline(
        load_mvp_config(Path("configs/mvp.json")),
        repo_root=Path.cwd(),
    )
    assert mvp_report["metrics"]["boundary"]["training_run"] is False
    assert mvp_report["metrics"]["final_test_status"] == "not_run"

    hard_negative_config = _write_hard_negative_config(tmp_path)
    assert mine_main(["--config", str(hard_negative_config)]) == 0
    assert (tmp_path / "hard-negatives" / "train.jsonl").is_file()
    assert (tmp_path / "hard-negatives" / "dev.jsonl").is_file()

    before = set(sys.modules)
    module = importlib.import_module("visdoc_retrieve.visual_zero_shot_backend")
    after = set(sys.modules)

    assert hasattr(module, "LocalVisualModelBackend")
    assert "torch" not in after - before
    assert "transformers" not in after - before
    assert "colpali_engine" not in after - before


def _readiness_module() -> ModuleType:
    try:
        return importlib.import_module("visdoc_retrieve.training_readiness")
    except ModuleNotFoundError as exc:
        if exc.name == "visdoc_retrieve.training_readiness":
            pytest.fail(f"missing training-readiness module: {exc}")
        raise


def _write_training_config(
    tmp_path: Path,
    *,
    train_hard_negatives_path: Path | str = "data/derived/hard_negatives/train.jsonl",
    allow_final_test: bool = False,
    dry_run: bool = True,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    ledger_path = tmp_path / "progress-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    config = {
        "base_model_name_or_path": "local-colpali-or-colqwen-placeholder",
        "model_revision": "phase-5a-placeholder",
        "local_model_path": "local-models/colpali-or-colqwen",
        "adapter_output_dir": ".local/training-readiness/adapters",
        "train_hard_negatives_path": str(train_hard_negatives_path),
        "dev_hard_negatives_path": "data/derived/hard_negatives/dev.jsonl",
        "corpus_path": "data/synthetic-smoke/pages.jsonl",
        "queries_path": "data/synthetic-smoke/queries.jsonl",
        "qrels_path": "data/synthetic-smoke/queries.jsonl",
        "candidate_universe_id": "evaluated_split_pages",
        "loss_type": "mock_pairwise_margin",
        "batch_size": 8,
        "gradient_accumulation_steps": 1,
        "max_steps": 1,
        "learning_rate": 0.0001,
        "seed": 17,
        "device": "cpu",
        "dry_run": dry_run,
        "allow_final_test": allow_final_test,
        "dry_run_sample_limit": 8,
        "report_timestamp_utc": "2026-07-01T00:00:00Z",
        "outputs": {
            "artifact_freeze": str(tmp_path / "reports" / "artifact-freeze.json"),
            "dataset_summary": str(tmp_path / "reports" / "dataset-summary.json"),
            "dry_run_card": str(tmp_path / "reports" / "dry-run-card.md"),
            "safety_check": str(tmp_path / "reports" / "safety-check.json"),
            "human_brief": str(tmp_path / "human-brief.md"),
            "progress_ledger": str(ledger_path),
        },
    }
    config_path = tmp_path / "train_lora_dry_run.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def _write_hard_negative_config(tmp_path: Path) -> Path:
    output_dir = tmp_path / "hard-negatives"
    ledger_path = tmp_path / "hard-negatives-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    config = {
        "name": "synthetic-smoke-hard-negatives-test",
        "pages_manifest": "data/synthetic-smoke/pages.jsonl",
        "queries_manifest": "data/synthetic-smoke/queries.jsonl",
        "evaluated_splits": ["train", "dev"],
        "candidate_universe": "evaluated_split_pages",
        "final_test_split": "test",
        "top_k_per_source": 3,
        "sources": {
            "bm25": {"enabled": True, "top_k": 3},
            "lexical_cosine": {"enabled": True, "top_k": 3},
            "bm25_lexical_rrf": {"enabled": True, "top_k": 3},
            "mock_visual": {"enabled": True, "top_k": 3},
            "same_document": {"enabled": True, "top_k": 3},
            "tag_aware": {"enabled": True, "top_k": 3},
        },
        "outputs": {
            "train_jsonl": str(output_dir / "train.jsonl"),
            "dev_jsonl": str(output_dir / "dev.jsonl"),
            "summary": str(output_dir / "mining-summary.json"),
            "leakage_check": str(output_dir / "leakage-check.json"),
            "run_card": str(output_dir / "run-card.md"),
            "human_brief": str(output_dir / "human-brief.html"),
            "progress_ledger": str(ledger_path),
        },
    }
    config_path = tmp_path / "hard_negatives.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
