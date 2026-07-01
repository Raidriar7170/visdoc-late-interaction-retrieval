"""Tests for Phase 5B real-training pilot launch gates."""

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

OPTIONAL_TRAINING_MODULES = {
    "torch",
    "transformers",
    "peft",
    "colpali_engine",
}


def test_pilot_config_parses_and_rejects_unsafe_flags(tmp_path: Path) -> None:
    pilot = _pilot_module()

    config = pilot.load_training_pilot_config(
        Path("configs/train_lora_pilot.local.example.json")
    )

    assert config.base_model_name_or_path == "local-colpali-or-colqwen-placeholder"
    assert config.local_model_path == Path("local-models/colpali-or-colqwen")
    assert config.model_revision == "phase-5b-placeholder"
    assert config.adapter_output_dir == Path(".local/training-pilot/adapters")
    assert config.train_hard_negatives_path == Path(
        "data/derived/hard_negatives/train.jsonl"
    )
    assert config.dev_hard_negatives_path == Path(
        "data/derived/hard_negatives/dev.jsonl"
    )
    assert config.queries_path == Path("data/derived/training-pilot/dev-queries.jsonl")
    assert config.qrels_path == Path("data/derived/training-pilot/dev-qrels.jsonl")
    assert config.candidate_universe_id == "evaluated_split_pages"
    assert config.loss_type == "lora_pairwise_maxsim"
    assert config.lora_r == 8
    assert config.lora_alpha == 16
    assert config.lora_dropout == pytest.approx(0.05)
    assert config.qlora is False
    assert config.batch_size == 1
    assert config.gradient_accumulation_steps == 1
    assert config.max_steps == 20
    assert config.learning_rate == pytest.approx(0.0001)
    assert config.seed == 17
    assert config.device == "cuda"
    assert config.allow_real_training is False
    assert config.allow_final_test is False
    assert config.save_adapter is True

    unsafe_final = _write_pilot_config(tmp_path, allow_final_test=True)
    with pytest.raises(pilot.TrainingPilotConfigError, match="allow_final_test"):
        pilot.load_training_pilot_config(unsafe_final)

    over_budget = _write_pilot_config(tmp_path, max_steps=21)
    with pytest.raises(pilot.TrainingPilotConfigError, match="max_steps"):
        pilot.load_training_pilot_config(over_budget)

    final_test_dev = _write_pilot_config(
        tmp_path,
        dev_hard_negatives_path="data/derived/hard_negatives/test.jsonl",
    )
    with pytest.raises(pilot.TrainingPilotConfigError, match="final test"):
        pilot.load_training_pilot_config(final_test_dev)

    final_test_queries = _write_pilot_config(
        tmp_path,
        queries_path="data/synthetic-smoke/queries.jsonl",
    )
    with pytest.raises(pilot.TrainingPilotConfigError, match="dev-only"):
        pilot.load_training_pilot_config(final_test_queries)

    final_test_qrels = _write_pilot_config(
        tmp_path,
        qrels_path="data/synthetic-smoke/queries.jsonl",
    )
    with pytest.raises(pilot.TrainingPilotConfigError, match="dev-only"):
        pilot.load_training_pilot_config(final_test_qrels)

    dev_labeled_test_page = tmp_path / "dev-labeled-test-page.jsonl"
    record = json.loads(
        Path("data/derived/training-pilot/dev-qrels.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    record["positive_page_ids"] = ["manual-c-p01"]
    record["source"]["page_id"] = "manual-c-p01"
    record["source"]["doc_id"] = "manual-c"
    dev_labeled_test_page.write_text(
        json.dumps(record, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dev_labeled_test_config = _write_pilot_config(
        tmp_path,
        qrels_path=dev_labeled_test_page,
    )
    with pytest.raises(pilot.TrainingPilotConfigError, match="final test page"):
        pilot.load_training_pilot_config(dev_labeled_test_config)


def test_default_pilot_cli_blocks_and_writes_evidence_without_optional_imports(
    tmp_path: Path,
) -> None:
    before = set(sys.modules)
    pilot = _pilot_module()
    after_import = set(sys.modules)
    assert not OPTIONAL_TRAINING_MODULES.intersection(after_import - before)

    config_path = _write_pilot_config(tmp_path, allow_real_training=False)
    exit_code = pilot.main(["--config", str(config_path)])
    after_run = set(sys.modules)

    assert exit_code == 2
    assert not OPTIONAL_TRAINING_MODULES.intersection(after_run - before)

    report_dir = tmp_path / "reports"
    environment = json.loads((report_dir / "environment-check.json").read_text())
    run_card = (report_dir / "blocked-run-card.md").read_text(encoding="utf-8")

    assert environment["schema"] == "training_pilot_environment_check/v1"
    assert environment["overall_status"] == "blocked"
    assert environment["real_training_executed"] is False
    assert environment["blocked_reasons"][0]["code"] == "allow_real_training_false"
    assert environment["gates"]["allow_final_test_false"]["passed"] is True
    assert environment["gates"]["allow_real_training_true"]["passed"] is False
    assert "blocked" in run_card
    assert "pilot" in run_card
    assert "dev-only" in run_card
    assert "not final benchmark" in run_card


def test_missing_model_and_cuda_unavailable_block_explicitly(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()

    missing_model_config = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=tmp_path / "missing-model",
    )
    missing_result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(missing_model_config),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: False,
    )
    assert missing_result["status"] == "blocked"
    assert missing_result["blocked_reasons"][0]["code"] == "missing_local_model_path"

    local_model = tmp_path / "local-model"
    local_model.mkdir()
    cuda_blocked_config = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
    )
    cuda_result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(cuda_blocked_config),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: False,
    )
    assert cuda_result["status"] == "blocked"
    assert cuda_result["blocked_reasons"][0]["code"] == "cuda_unavailable"


def test_cuda_is_not_probed_before_adapter_ignore_gate_passes(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    config_path = _write_pilot_config(
        tmp_path,
        adapter_output_dir=tmp_path / "not-ignored-adapters",
        allow_real_training=True,
        local_model_path=local_model,
    )

    def fail_if_probed() -> bool:
        raise AssertionError("CUDA should not be probed before ignore gate passes")

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=fail_if_probed,
    )

    assert result["status"] == "blocked"
    assert result["blocked_reasons"][0]["code"] == "adapter_output_not_ignored"


def test_dev_eval_manifest_and_safety_outputs_are_honest(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    config_path = _write_pilot_config(tmp_path)

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    assert result["status"] == "blocked"
    report_dir = tmp_path / "reports"
    safety = json.loads((report_dir / "safety-check.json").read_text())
    dev_eval = json.loads((report_dir / "dev-eval-schema.json").read_text())
    manifest = json.loads(
        (report_dir / "adapter-manifest.example.json").read_text()
    )
    brief = (tmp_path / "human-brief.html").read_text(encoding="utf-8")
    ledger = yaml.safe_load((tmp_path / "progress-ledger.yaml").read_text())

    assert safety["training_executed"] is False
    assert safety["model_download_executed"] is False
    assert safety["network_used"] is False
    assert safety["final_test_used"] is False
    assert safety["adapter_checkpoint_committed"] is False
    assert safety["model_weights_committed"] is False
    assert safety["forbidden_artifact_scan"]["model_weight_paths"] == []
    assert safety["benchmark_claim_added"] is False
    assert safety["mock_visual_result_reported_as_real"] is False

    assert dev_eval["schema"] == "training_pilot_dev_eval/v1"
    assert dev_eval["status"] == "not_run"
    assert dev_eval["scope"] == "dev-only"
    assert dev_eval["final_test_used"] is False
    assert dev_eval["metrics"]["recall_at_1"] is None
    assert dev_eval["metrics"]["mrr"] is None
    assert dev_eval["improvement_claim"] is None

    assert manifest["schema"] == "training_pilot_adapter_manifest/v1"
    assert manifest["adapter_output_dir"] == ".local/training-pilot/adapters"
    assert manifest["final_test_used"] is False
    assert manifest["pilot_status"] == "blocked"
    assert manifest["adapter_checkpoint_created"] is False
    assert len(manifest["hard_negative_artifact_hash"]) == 64
    assert len(manifest["train_config_hash"]) == 64

    assert "Phase 5B" in brief
    assert "默认不训练" in brief
    assert "final test" in brief
    assert ledger["training_pilot_status"]["status"] == "blocked"
    assert ledger["training_pilot_status"]["final_test_evaluation"] == "not_run"
    assert ledger["training_pilot_status"]["benchmark_claim"] == "none"


def test_safety_check_reports_tracked_forbidden_artifacts(tmp_path: Path) -> None:
    pilot = _pilot_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text(".local/\n", encoding="utf-8")
    weights_dir = repo_root / "tracked"
    weights_dir.mkdir()
    (weights_dir / "model.safetensors").write_text(
        "not a real weight",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "-f", "tracked/model.safetensors"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    config_path = _write_pilot_config(tmp_path)

    pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=repo_root,
        environ={},
        cuda_available=lambda: False,
    )

    safety = json.loads((tmp_path / "reports" / "safety-check.json").read_text())
    assert safety["model_weights_committed"] is True
    assert safety["forbidden_artifact_scan"]["model_weight_paths"] == [
        "tracked/model.safetensors"
    ]


def test_real_training_artifact_paths_are_ignored() -> None:
    paths = [
        ".local/training-pilot/adapters/example",
        "local-models/colpali-or-colqwen/model.safetensors",
        ".cache/visdoc-training/cache.bin",
        "wandb/run-1/config.yaml",
        "runs/training-pilot/events.out.tfevents",
        "checkpoints/visdoc/adapter.pt",
    ]
    completed = subprocess.run(
        ["git", "check-ignore", *paths],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    ignored = set(completed.stdout.splitlines())
    assert ignored == set(paths)


def test_existing_cli_surfaces_still_work(tmp_path: Path) -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.run_mvp",
            "--config",
            "configs/mvp.json",
        ],
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.mine_hard_negatives",
            "--config",
            str(_write_hard_negative_config(tmp_path)),
        ],
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.train_lora_dry_run",
            "--config",
            str(_write_dry_run_config(tmp_path)),
        ],
    ]
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env={**os.environ, "PYTHONPATH": "src"},
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def _pilot_module() -> ModuleType:
    try:
        return importlib.import_module("visdoc_retrieve.train_lora_pilot")
    except ModuleNotFoundError as exc:
        if exc.name == "visdoc_retrieve.train_lora_pilot":
            pytest.fail(f"missing training-pilot module: {exc}")
        raise


def _write_pilot_config(
    tmp_path: Path,
    *,
    adapter_output_dir: Path | str = ".local/training-pilot/adapters",
    allow_real_training: bool = False,
    allow_final_test: bool = False,
    queries_path: Path | str = "data/derived/training-pilot/dev-queries.jsonl",
    qrels_path: Path | str = "data/derived/training-pilot/dev-qrels.jsonl",
    local_model_path: Path | str = "local-models/colpali-or-colqwen",
    dev_hard_negatives_path: Path | str = "data/derived/hard_negatives/dev.jsonl",
    max_steps: int = 20,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    ledger_path = tmp_path / "progress-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    config = {
        "adapter_output_dir": str(adapter_output_dir),
        "allow_final_test": allow_final_test,
        "allow_real_training": allow_real_training,
        "base_model_name_or_path": "local-colpali-or-colqwen-placeholder",
        "batch_size": 1,
        "candidate_universe_id": "evaluated_split_pages",
        "corpus_path": "data/synthetic-smoke/pages.jsonl",
        "dev_hard_negatives_path": str(dev_hard_negatives_path),
        "device": "cuda",
        "gradient_accumulation_steps": 1,
        "learning_rate": 0.0001,
        "local_model_path": str(local_model_path),
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "lora_r": 8,
        "loss_type": "lora_pairwise_maxsim",
        "max_steps": max_steps,
        "model_revision": "phase-5b-placeholder",
        "outputs": {
            "adapter_manifest": str(
                tmp_path / "reports" / "adapter-manifest.example.json"
            ),
            "blocked_run_card": str(tmp_path / "reports" / "blocked-run-card.md"),
            "dev_eval_schema": str(tmp_path / "reports" / "dev-eval-schema.json"),
            "environment_check": str(
                tmp_path / "reports" / "environment-check.json"
            ),
            "human_brief": str(tmp_path / "human-brief.html"),
            "pilot_run_card": str(tmp_path / "reports" / "pilot-run-card.md"),
            "progress_ledger": str(ledger_path),
            "safety_check": str(tmp_path / "reports" / "safety-check.json"),
        },
        "qlora": False,
        "qrels_path": str(qrels_path),
        "queries_path": str(queries_path),
        "report_timestamp_utc": "2026-07-01T00:00:00Z",
        "save_adapter": True,
        "seed": 17,
        "train_hard_negatives_path": "data/derived/hard_negatives/train.jsonl",
    }
    config_path = tmp_path / "train_lora_pilot.local.example.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path


def _write_dry_run_config(tmp_path: Path) -> Path:
    output_dir = tmp_path / "training-readiness"
    ledger_path = tmp_path / "training-readiness-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    config = {
        "adapter_output_dir": ".local/training-readiness/adapters",
        "allow_final_test": False,
        "base_model_name_or_path": "local-colpali-or-colqwen-placeholder",
        "batch_size": 8,
        "candidate_universe_id": "evaluated_split_pages",
        "corpus_path": "data/synthetic-smoke/pages.jsonl",
        "dev_hard_negatives_path": "data/derived/hard_negatives/dev.jsonl",
        "device": "cpu",
        "dry_run": True,
        "dry_run_sample_limit": 8,
        "gradient_accumulation_steps": 1,
        "learning_rate": 0.0001,
        "local_model_path": "local-models/colpali-or-colqwen",
        "loss_type": "mock_pairwise_margin",
        "max_steps": 1,
        "model_revision": "phase-5a-placeholder",
        "outputs": {
            "artifact_freeze": str(output_dir / "artifact-freeze.json"),
            "dataset_summary": str(output_dir / "dataset-summary.json"),
            "dry_run_card": str(output_dir / "dry-run-card.md"),
            "human_brief": str(output_dir / "human-brief.md"),
            "progress_ledger": str(ledger_path),
            "safety_check": str(output_dir / "safety-check.json"),
        },
        "qrels_path": "data/synthetic-smoke/queries.jsonl",
        "queries_path": "data/synthetic-smoke/queries.jsonl",
        "report_timestamp_utc": "2026-07-01T00:00:00Z",
        "seed": 17,
        "train_hard_negatives_path": "data/derived/hard_negatives/train.jsonl",
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
        "candidate_universe": "evaluated_split_pages",
        "evaluated_splits": ["train", "dev"],
        "final_test_split": "test",
        "name": "synthetic-smoke-hard-negatives-test",
        "outputs": {
            "dev_jsonl": str(output_dir / "dev.jsonl"),
            "human_brief": str(output_dir / "human-brief.html"),
            "leakage_check": str(output_dir / "leakage-check.json"),
            "progress_ledger": str(ledger_path),
            "run_card": str(output_dir / "run-card.md"),
            "summary": str(output_dir / "mining-summary.json"),
            "train_jsonl": str(output_dir / "train.jsonl"),
        },
        "pages_manifest": "data/synthetic-smoke/pages.jsonl",
        "queries_manifest": "data/synthetic-smoke/queries.jsonl",
        "sources": {
            "bm25": {"enabled": True, "top_k": 3},
            "bm25_lexical_rrf": {"enabled": True, "top_k": 3},
            "lexical_cosine": {"enabled": True, "top_k": 3},
            "mock_visual": {
                "enabled": True,
                "provider": "deterministic_mock",
                "top_k": 3,
            },
            "same_document": {"enabled": True, "top_k": 3},
            "tag_aware": {"enabled": True, "top_k": 3},
        },
        "top_k_per_source": 3,
    }
    config_path = tmp_path / "hard_negatives.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path
