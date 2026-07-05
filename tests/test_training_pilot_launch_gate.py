"""Tests for Phase 5D real-training pilot backend wiring gates."""

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
    assert config.model_revision == "phase-5d-local-files-only-placeholder"
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
    assert config.sample_limit == 8
    assert config.learning_rate == pytest.approx(0.0001)
    assert config.seed == 17
    assert config.device == "cuda"
    assert config.allow_real_training is False
    assert config.allow_final_test is False
    assert config.save_adapter is False
    assert config.local_files_only is True
    assert config.backend_dependency == "colpali_engine"
    assert config.phase_metadata.schema_id == "phase_5d"
    assert config.phase_metadata.phase_label == "5D"
    assert config.phase_metadata.change_name == "add-real-training-backend-wiring"
    assert config.phase_metadata.ledger_section == "training_pilot_phase_5d_status"

    unsafe_final = _write_pilot_config(tmp_path, allow_final_test=True)
    with pytest.raises(pilot.TrainingPilotConfigError, match="allow_final_test"):
        pilot.load_training_pilot_config(unsafe_final)

    over_budget = _write_pilot_config(tmp_path, max_steps=21)
    with pytest.raises(pilot.TrainingPilotConfigError, match="max_steps"):
        pilot.load_training_pilot_config(over_budget)

    over_sample_limit = _write_pilot_config(tmp_path, sample_limit=9)
    with pytest.raises(pilot.TrainingPilotConfigError, match="sample_limit"):
        pilot.load_training_pilot_config(over_sample_limit)

    network_model_loading = _write_pilot_config(tmp_path, local_files_only=False)
    with pytest.raises(pilot.TrainingPilotConfigError, match="local_files_only"):
        pilot.load_training_pilot_config(network_model_loading)

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
    backend = importlib.import_module("visdoc_retrieve.lora_training_backend")
    after_import = set(sys.modules)
    assert not OPTIONAL_TRAINING_MODULES.intersection(after_import - before)
    assert backend is not None

    config_path = _write_pilot_config(tmp_path, allow_real_training=False)
    exit_code = pilot.main(["--config", str(config_path)])
    after_run = set(sys.modules)

    assert exit_code == 2
    assert not OPTIONAL_TRAINING_MODULES.intersection(after_run - before)

    report_dir = tmp_path / "reports"
    environment = json.loads(
        (report_dir / "phase-5d-environment-check.json").read_text()
    )
    run_card = (
        report_dir / "phase-5d-blocked-run-card.md"
    ).read_text(encoding="utf-8")

    assert environment["schema"] == "training_pilot_phase_5d_environment_check/v1"
    assert environment["overall_status"] == "blocked"
    assert environment["real_training_executed"] is False
    assert environment["config"]["sample_limit"] == 8
    assert environment["config"]["local_files_only"] is True
    assert environment["blocked_reasons"][0]["code"] == "allow_real_training_false"
    assert environment["gates"]["artifact_freeze_hashes_match"]["passed"] is True
    assert environment["gates"]["hard_negative_files_exist"]["passed"] is True
    assert (
        environment["gates"]["hard_negative_candidate_universe_matches"]["passed"]
        is True
    )
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


def test_optional_dependency_missing_blocks_after_all_non_import_gates(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
        backend_dependency="visdoc_missing_backend_dependency",
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: True,
    )

    assert result["status"] == "blocked"
    assert result["blocked_reasons"][0]["code"] == (
        "optional_training_dependency_missing"
    )
    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert environment["training_result"]["training_executed"] is False
    assert "visdoc_missing_backend_dependency" in environment["training_result"][
        "missing_dependencies"
    ]


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


def test_artifact_freeze_hash_mismatch_blocks_before_training(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    freeze = json.loads(
        Path("reports/training-readiness/artifact-freeze.json").read_text(
            encoding="utf-8"
        )
    )
    freeze["artifacts"]["train_hard_negatives"]["sha256"] = "0" * 64
    freeze_path = tmp_path / "artifact-freeze-mismatch.json"
    freeze_path.write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    config_path = _write_pilot_config(tmp_path, artifact_freeze_path=freeze_path)

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert result["status"] == "blocked"
    assert "artifact_freeze_mismatch" in {
        reason["code"] for reason in result["blocked_reasons"]
    }
    assert environment["gates"]["artifact_freeze_hashes_match"]["passed"] is False
    assert "train_hard_negatives" in environment["gates"][
        "artifact_freeze_hashes_match"
    ]["message"]


def test_missing_hard_negative_file_blocks_clearly(tmp_path: Path) -> None:
    pilot = _pilot_module()
    missing_train = tmp_path / "missing-train.jsonl"
    config_path = _write_pilot_config(
        tmp_path,
        train_hard_negatives_path=missing_train,
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert result["status"] == "blocked"
    assert "hard_negative_file_missing" in {
        reason["code"] for reason in result["blocked_reasons"]
    }
    assert environment["gates"]["hard_negative_files_exist"]["passed"] is False
    assert str(missing_train) in environment["gates"]["hard_negative_files_exist"][
        "message"
    ]


def test_hard_negative_candidate_universe_mismatch_blocks_clearly(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    mismatched_train = tmp_path / "train-candidate-universe-mismatch.jsonl"
    first_record = json.loads(
        Path("data/derived/hard_negatives/train.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    first_record["candidate_universe_id"] = "all_pages"
    mismatched_train.write_text(
        json.dumps(first_record, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    config_path = _write_pilot_config(
        tmp_path,
        train_hard_negatives_path=mismatched_train,
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert result["status"] == "blocked"
    assert "hard_negative_candidate_universe_mismatch" in {
        reason["code"] for reason in result["blocked_reasons"]
    }
    assert (
        environment["gates"]["hard_negative_candidate_universe_matches"]["passed"]
        is False
    )
    assert "all_pages" in environment["gates"][
        "hard_negative_candidate_universe_matches"
    ]["message"]


def test_malformed_artifact_freeze_blocks_with_evidence(tmp_path: Path) -> None:
    pilot = _pilot_module()
    bad_freeze = tmp_path / "bad-artifact-freeze.json"
    bad_freeze.write_text("{not-json", encoding="utf-8")
    config_path = _write_pilot_config(tmp_path, artifact_freeze_path=bad_freeze)

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert result["status"] == "blocked"
    assert "artifact_freeze_invalid" in {
        reason["code"] for reason in result["blocked_reasons"]
    }
    assert environment["gates"]["artifact_freeze_hashes_match"]["passed"] is False
    assert "not valid JSON" in environment["gates"][
        "artifact_freeze_hashes_match"
    ]["message"]


def test_malformed_hard_negative_jsonl_blocks_with_evidence(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    bad_train = tmp_path / "bad-train.jsonl"
    bad_train.write_text("{not-json\n", encoding="utf-8")
    config_path = _write_pilot_config(
        tmp_path,
        train_hard_negatives_path=bad_train,
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={},
        cuda_available=lambda: False,
    )

    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert result["status"] == "blocked"
    assert "hard_negative_file_invalid" in {
        reason["code"] for reason in result["blocked_reasons"]
    }
    assert (
        environment["gates"]["hard_negative_candidate_universe_matches"]["passed"]
        is False
    )
    assert "not valid JSON" in environment["gates"][
        "hard_negative_candidate_universe_matches"
    ]["message"]


def test_cli_repo_root_resolves_repo_relative_validation_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pilot = _pilot_module()
    repo_root = Path.cwd()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    config_path = _write_pilot_config(tmp_path)

    monkeypatch.chdir(outside_dir)
    exit_code = pilot.main(
        [
            "--repo-root",
            str(repo_root),
            "--config",
            str(config_path),
        ]
    )

    assert exit_code == 2
    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert environment["overall_status"] == "blocked"
    assert environment["gates"]["artifact_freeze_hashes_match"]["passed"] is True
    assert environment["gates"]["hard_negative_files_exist"]["passed"] is True
    assert (
        environment["gates"]["hard_negative_candidate_universe_matches"]["passed"]
        is True
    )


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
    safety = json.loads((report_dir / "phase-5d-safety-check.json").read_text())
    dev_eval = json.loads((report_dir / "phase-5d-dev-eval-schema.json").read_text())
    manifest = json.loads(
        (report_dir / "phase-5d-adapter-manifest.sanitized.json").read_text()
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
    assert safety["pilot_loss_reported_as_model_improvement"] is False

    assert dev_eval["schema"] == "training_pilot_phase_5d_dev_eval/v1"
    assert dev_eval["status"] == "not_run"
    assert dev_eval["scope"] == "dev-only"
    assert dev_eval["final_test_used"] is False
    assert dev_eval["metrics"]["recall_at_1"] is None
    assert dev_eval["metrics"]["mrr"] is None
    assert dev_eval["improvement_claim"] is None

    assert manifest["schema"] == "training_pilot_phase_5d_adapter_manifest_sanitized/v1"
    assert manifest["adapter_output_dir"] == ".local/training-pilot/adapters"
    assert manifest["final_test_used"] is False
    assert manifest["pilot_status"] == "blocked"
    assert manifest["adapter_checkpoint_created"] is False
    assert manifest["sample_limit"] == 8
    assert manifest["effective_training_sample_count"] == 0
    assert len(manifest["hard_negative_artifact_hash"]) == 64
    assert len(manifest["train_config_hash"]) == 64

    assert "Phase 5D" in brief
    assert "backend wiring" in brief
    assert "final test" in brief
    assert ledger["training_pilot_phase_5d_status"]["status"] == "blocked"
    assert (
        ledger["training_pilot_phase_5d_status"]["final_test_evaluation"]
        == "not_run"
    )
    assert ledger["training_pilot_phase_5d_status"]["benchmark_claim"] == "none"


def test_train_sample_loader_caps_train_only_records() -> None:
    backend = importlib.import_module("visdoc_retrieve.lora_training_backend")

    samples = backend.load_train_hard_negative_samples(
        Path("data/derived/hard_negatives/train.jsonl"),
        repo_root=Path.cwd(),
        sample_limit=3,
        candidate_universe_id="evaluated_split_pages",
    )

    assert len(samples) == 3
    assert {sample["split"] for sample in samples} == {"train"}
    assert all("manual-c" not in sample["query_id"] for sample in samples)


def test_fake_backend_runner_can_record_pilot_run_without_final_test(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
        sample_limit=4,
        save_adapter=True,
    )

    def fake_backend_runner(config, *, repo_root: Path) -> dict[str, object]:
        assert config.sample_limit == 4
        assert str(config.train_hard_negatives_path).endswith("train.jsonl")
        assert "test" not in str(config.train_hard_negatives_path)
        return {
            "status": "pilot_run",
            "training_executed": True,
            "effective_training_sample_count": 4,
            "adapter_checkpoint_created": True,
            "adapter_checkpoint_path": str(config.adapter_output_dir),
            "loss": 0.0,
            "final_test_used": False,
        }

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: True,
        training_backend_runner=fake_backend_runner,
    )

    assert result["status"] == "pilot_run"
    report_dir = tmp_path / "reports"
    manifest = json.loads(
        (report_dir / "phase-5d-adapter-manifest.sanitized.json").read_text()
    )
    dev_eval = json.loads((report_dir / "phase-5d-dev-eval-schema.json").read_text())
    safety = json.loads((report_dir / "phase-5d-safety-check.json").read_text())
    ledger = yaml.safe_load((tmp_path / "progress-ledger.yaml").read_text())
    run_card = (
        report_dir / "phase-5d-pilot-run-card.md"
    ).read_text(encoding="utf-8")

    assert manifest["pilot_status"] == "pilot_run"
    assert manifest["adapter_checkpoint_created"] is True
    assert manifest["effective_training_sample_count"] == 4
    assert manifest["pilot_loss_reported_as_model_improvement"] is False
    assert dev_eval["scope"] == "dev-only"
    assert dev_eval["final_test_used"] is False
    assert dev_eval["improvement_claim"] is None
    assert safety["pilot_loss_reported_as_model_improvement"] is False
    assert ledger["training_pilot_phase_5d_status"]["evidence"]["run_card"] == (
        str(report_dir / "phase-5d-pilot-run-card.md")
    )
    assert "not final benchmark" in run_card
    assert "improvement" not in run_card.lower()


def test_phase_metadata_override_updates_public_evidence_and_ledger(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
        sample_limit=4,
        save_adapter=True,
        phase_metadata={
            "schema_id": "phase_5i",
            "phase_label": "5I",
            "change_name": "run-phase-5i-gated-tiny-real-pilot",
            "title": "Phase 5I Gated Tiny Real Pilot",
            "ledger_section": "training_pilot_phase_5i_status",
            "summary_zh": "Phase 5I 在 A100 上尝试一次 gated tiny real-pilot；",
            "recommended_next_step_zh": "基于本次 pilot 结果决定是否进入下一阶段。",
        },
        outputs={
            "adapter_manifest": str(
                tmp_path
                / "reports"
                / "phase-5i-adapter-manifest.sanitized.json"
            ),
            "blocked_run_card": str(
                tmp_path / "reports" / "phase-5i-blocked-run-card.md"
            ),
            "dev_eval_schema": str(tmp_path / "reports" / "phase-5i-dev-eval.json"),
            "environment_check": str(
                tmp_path / "reports" / "phase-5i-environment-check.json"
            ),
            "human_brief": str(tmp_path / "phase-5i-human-brief.html"),
            "pilot_run_card": str(
                tmp_path / "reports" / "phase-5i-pilot-run-card.md"
            ),
            "progress_ledger": str(tmp_path / "progress-ledger.yaml"),
            "safety_check": str(
                tmp_path / "reports" / "phase-5i-safety-check.json"
            ),
        },
    )

    def fake_backend_runner(config, *, repo_root: Path) -> dict[str, object]:
        return {
            "status": "pilot_run",
            "training_executed": True,
            "effective_training_sample_count": 4,
            "adapter_checkpoint_created": True,
            "adapter_checkpoint_path": str(config.adapter_output_dir),
            "final_test_used": False,
        }

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: True,
        training_backend_runner=fake_backend_runner,
    )

    assert result["status"] == "pilot_run"
    report_dir = tmp_path / "reports"
    environment = json.loads(
        (report_dir / "phase-5i-environment-check.json").read_text()
    )
    safety = json.loads((report_dir / "phase-5i-safety-check.json").read_text())
    dev_eval = json.loads((report_dir / "phase-5i-dev-eval.json").read_text())
    manifest = json.loads(
        (report_dir / "phase-5i-adapter-manifest.sanitized.json").read_text()
    )
    run_card = (
        report_dir / "phase-5i-pilot-run-card.md"
    ).read_text(encoding="utf-8")
    brief = (tmp_path / "phase-5i-human-brief.html").read_text(encoding="utf-8")
    ledger = yaml.safe_load((tmp_path / "progress-ledger.yaml").read_text())

    assert environment["schema"] == "training_pilot_phase_5i_environment_check/v1"
    assert environment["phase"] == "5I"
    assert environment["change"] == "run-phase-5i-gated-tiny-real-pilot"
    assert safety["schema"] == "training_pilot_phase_5i_safety_check/v1"
    assert dev_eval["schema"] == "training_pilot_phase_5i_dev_eval/v1"
    assert (
        manifest["schema"]
        == "training_pilot_phase_5i_adapter_manifest_sanitized/v1"
    )
    assert "Phase 5I Gated Tiny Real Pilot" in run_card
    assert "Phase 5I Gated Tiny Real Pilot" in brief
    assert "phase-5i-pilot-run-card.md" in brief
    assert ledger["training_pilot_phase_5i_status"]["status"] == "pilot_run"
    assert (
        ledger["training_pilot_phase_5i_status"]["change"]
        == "run-phase-5i-gated-tiny-real-pilot"
    )
    assert (
        ledger["training_pilot_phase_5i_status"]["evidence"]["run_card"]
        == str(report_dir / "phase-5i-pilot-run-card.md")
    )


def test_transformers_peft_probe_blocks_without_real_training_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
        backend_dependency="visdoc_fake_backend_without_runner",
        save_adapter=True,
    )
    fake_backend = ModuleType("visdoc_fake_backend_without_runner")
    fake_transformers = ModuleType("transformers")
    fake_peft = ModuleType("peft")

    class FakeModel:
        def train(self) -> None:
            pass

        def save_pretrained(self, path: str) -> None:
            Path(path).mkdir(parents=True, exist_ok=True)

    class FakeAutoModel:
        @staticmethod
        def from_pretrained(path: str, *, local_files_only: bool) -> FakeModel:
            assert Path(path) == local_model
            assert local_files_only is True
            return FakeModel()

    class FakeLoraConfig:
        def __init__(self, **_: object) -> None:
            pass

    def fake_get_peft_model(model: FakeModel, _: FakeLoraConfig) -> FakeModel:
        return model

    fake_transformers.AutoModel = FakeAutoModel
    fake_peft.LoraConfig = FakeLoraConfig
    fake_peft.get_peft_model = fake_get_peft_model
    monkeypatch.setitem(sys.modules, "torch", ModuleType("torch"))
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setitem(sys.modules, "peft", fake_peft)
    monkeypatch.setitem(
        sys.modules,
        "visdoc_fake_backend_without_runner",
        fake_backend,
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: True,
    )

    assert result["status"] == "blocked"
    assert result["blocked_reasons"][0]["code"] == "backend_training_step_unavailable"
    environment = json.loads(
        (tmp_path / "reports" / "phase-5d-environment-check.json").read_text()
    )
    assert environment["training_result"]["training_executed"] is False
    assert environment["training_result"]["adapter_checkpoint_created"] is False


def test_unsafe_backend_result_is_downgraded_to_blocked(
    tmp_path: Path,
) -> None:
    pilot = _pilot_module()
    local_model = tmp_path / "local-model"
    local_model.mkdir()
    private_adapter = tmp_path / "private-adapter"
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=local_model,
        sample_limit=4,
        save_adapter=True,
    )

    def unsafe_backend_runner(config, *, repo_root: Path) -> dict[str, object]:
        return {
            "status": "pilot_run",
            "training_executed": True,
            "effective_training_sample_count": 9,
            "adapter_checkpoint_created": True,
            "adapter_checkpoint_path": str(private_adapter),
            "final_test_used": True,
            "benchmark_improvement_claim": True,
            "loss": 0.12,
        }

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: True,
        training_backend_runner=unsafe_backend_runner,
    )

    assert result["status"] == "blocked"
    assert result["blocked_reasons"][0]["code"] == "unsafe_backend_result"
    manifest = json.loads(
        (
            tmp_path
            / "reports"
            / "phase-5d-adapter-manifest.sanitized.json"
        ).read_text()
    )
    assert manifest["adapter_checkpoint_created"] is False
    assert str(private_adapter) not in json.dumps(manifest)
    assert manifest["final_test_used"] is False
    assert manifest["benchmark_improvement_claim"] is False


def test_local_model_path_is_redacted_in_public_evidence(tmp_path: Path) -> None:
    pilot = _pilot_module()
    private_model = tmp_path / "private" / "colpali"
    config_path = _write_pilot_config(
        tmp_path,
        allow_real_training=True,
        local_model_path=private_model,
    )

    result = pilot.run_training_pilot_gate(
        pilot.load_training_pilot_config(config_path),
        repo_root=Path.cwd(),
        environ={"VISDOC_ENABLE_REAL_TRAINING": "1"},
        cuda_available=lambda: False,
    )

    assert result["status"] == "blocked"
    report_dir = tmp_path / "reports"
    environment_text = (
        report_dir / "phase-5d-environment-check.json"
    ).read_text(encoding="utf-8")
    run_card = (
        report_dir / "phase-5d-blocked-run-card.md"
    ).read_text(encoding="utf-8")
    assert str(private_model) not in environment_text
    assert str(private_model) not in run_card
    environment = json.loads(environment_text)
    assert environment["config"]["local_model_path"] == "<redacted-local-model-path>"
    assert environment["local_model_path_summary"]["redacted"] is True


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

    safety = json.loads(
        (tmp_path / "reports" / "phase-5d-safety-check.json").read_text()
    )
    assert safety["model_weights_committed"] is True
    assert safety["forbidden_artifact_scan"]["model_weight_paths"] == [
        "tracked/model.safetensors"
    ]


def test_real_training_artifact_paths_are_ignored() -> None:
    paths = [
        ".local/training-pilot/adapters/example",
        "local/train_lora_pilot.phase5i.local.json",
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
    artifact_freeze_path: Path | str = (
        "reports/training-readiness/artifact-freeze.json"
    ),
    backend_dependency: str = "colpali_engine",
    queries_path: Path | str = "data/derived/training-pilot/dev-queries.jsonl",
    qrels_path: Path | str = "data/derived/training-pilot/dev-qrels.jsonl",
    local_model_path: Path | str = "local-models/colpali-or-colqwen",
    local_files_only: bool = True,
    train_hard_negatives_path: Path | str = (
        "data/derived/hard_negatives/train.jsonl"
    ),
    dev_hard_negatives_path: Path | str = "data/derived/hard_negatives/dev.jsonl",
    max_steps: int = 20,
    sample_limit: int = 8,
    save_adapter: bool = False,
    phase_metadata: dict[str, object] | None = None,
    outputs: dict[str, str] | None = None,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    ledger_path = tmp_path / "progress-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    config_outputs = outputs or {
        "adapter_manifest": str(
            tmp_path
            / "reports"
            / "phase-5d-adapter-manifest.sanitized.json"
        ),
        "blocked_run_card": str(
            tmp_path / "reports" / "phase-5d-blocked-run-card.md"
        ),
        "dev_eval_schema": str(
            tmp_path / "reports" / "phase-5d-dev-eval-schema.json"
        ),
        "environment_check": str(
            tmp_path / "reports" / "phase-5d-environment-check.json"
        ),
        "human_brief": str(tmp_path / "human-brief.html"),
        "pilot_run_card": str(
            tmp_path / "reports" / "phase-5d-pilot-run-card.md"
        ),
        "progress_ledger": str(ledger_path),
        "safety_check": str(
            tmp_path / "reports" / "phase-5d-safety-check.json"
        ),
    }
    config = {
        "adapter_output_dir": str(adapter_output_dir),
        "allow_final_test": allow_final_test,
        "allow_real_training": allow_real_training,
        "artifact_freeze_path": str(artifact_freeze_path),
        "base_model_name_or_path": "local-colpali-or-colqwen-placeholder",
        "batch_size": 1,
        "backend_dependency": backend_dependency,
        "candidate_universe_id": "evaluated_split_pages",
        "corpus_path": "data/synthetic-smoke/pages.jsonl",
        "dev_hard_negatives_path": str(dev_hard_negatives_path),
        "device": "cuda",
        "gradient_accumulation_steps": 1,
        "learning_rate": 0.0001,
        "local_files_only": local_files_only,
        "local_model_path": str(local_model_path),
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "lora_r": 8,
        "loss_type": "lora_pairwise_maxsim",
        "max_steps": max_steps,
        "model_revision": "phase-5d-local-files-only-placeholder",
        "outputs": config_outputs,
        "phase_metadata": phase_metadata or {
            "schema_id": "phase_5d",
            "phase_label": "5D",
            "change_name": "add-real-training-backend-wiring",
            "title": "Phase 5D Real Training Backend Wiring",
            "ledger_section": "training_pilot_phase_5d_status",
            "summary_zh": "Phase 5D 完成 train_lora_pilot 的 backend wiring 检查点；",
            "recommended_next_step_zh": (
                "在具备本地模型和 CUDA 的 A100 环境中运行一次小预算 pilot，"
                "或继续记录 blocked evidence。"
            ),
        },
        "qlora": False,
        "qrels_path": str(qrels_path),
        "queries_path": str(queries_path),
        "report_timestamp_utc": "2026-07-01T00:00:00Z",
        "sample_limit": sample_limit,
        "save_adapter": save_adapter,
        "seed": 17,
        "train_hard_negatives_path": str(train_hard_negatives_path),
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
