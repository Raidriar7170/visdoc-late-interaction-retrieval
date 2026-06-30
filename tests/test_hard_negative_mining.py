"""Tests for deterministic hard-negative mining."""

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

from visdoc_retrieve.data_schema import ValidationError, load_jsonl
from visdoc_retrieve.mvp_pipeline import load_mvp_config, run_mvp_pipeline


def test_hard_negative_schema_round_trip_dedupes_and_orders(tmp_path: Path) -> None:
    miner = _miner_module()
    records = (
        miner.HardNegativeRecord(
            query_id="q-b",
            positive_page_id="p-pos",
            negative_page_id="p-neg-2",
            split="train",
            negative_source="bm25",
            rank=2,
            score=0.2,
            candidate_universe_id="evaluated_split_pages",
            reason="ranked_wrong_page",
            evidence={"method": "bm25"},
        ),
        miner.HardNegativeRecord(
            query_id="q-a",
            positive_page_id="p-pos",
            negative_page_id="p-neg-1",
            split="train",
            negative_source="bm25",
            rank=1,
            score=0.9,
            candidate_universe_id="evaluated_split_pages",
            reason="ranked_wrong_page",
            evidence={"method": "bm25"},
        ),
        miner.HardNegativeRecord(
            query_id="q-a",
            positive_page_id="p-pos",
            negative_page_id="p-neg-1",
            split="train",
            negative_source="bm25",
            rank=3,
            score=0.1,
            candidate_universe_id="evaluated_split_pages",
            reason="duplicate_lower_rank",
            evidence={"method": "bm25"},
        ),
    )

    ordered = miner.dedupe_and_sort_hard_negatives(records)

    assert [record.query_id for record in ordered] == ["q-a", "q-b"]
    assert [record.rank for record in ordered] == [1, 2]

    output = tmp_path / "train.jsonl"
    miner.write_hard_negative_jsonl(output, ordered)

    loaded = miner.load_hard_negative_jsonl(output)
    assert loaded == ordered

    raw = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert set(raw[0]) == {
        "candidate_universe_id",
        "evidence",
        "negative_page_id",
        "negative_source",
        "positive_page_id",
        "query_id",
        "rank",
        "reason",
        "score",
        "split",
    }


def test_leakage_checks_reject_positive_and_test_split_negatives() -> None:
    miner = _miner_module()
    pages = load_jsonl(Path("data/synthetic-smoke/pages.jsonl"))
    queries = load_jsonl(Path("data/synthetic-smoke/queries.jsonl"))

    positive_as_negative = miner.HardNegativeRecord(
        query_id="manual-a-p01-q01",
        positive_page_id="manual-a-p01",
        negative_page_id="manual-a-p01",
        split="train",
        negative_source="bm25",
        rank=1,
        score=1.0,
        candidate_universe_id="evaluated_split_pages",
        reason="invalid_positive",
        evidence={"method": "bm25"},
    )
    with pytest.raises(ValidationError, match="negative_page_id.*positive"):
        miner.validate_hard_negative_leakage(
            (positive_as_negative,),
            pages=pages,
            queries=queries,
            final_test_split="test",
        )

    test_split_negative = miner.HardNegativeRecord(
        query_id="manual-a-p01-q01",
        positive_page_id="manual-a-p01",
        negative_page_id="manual-c-p01",
        split="train",
        negative_source="bm25",
        rank=1,
        score=1.0,
        candidate_universe_id="all_pages",
        reason="invalid_test_split",
        evidence={"method": "bm25"},
    )
    with pytest.raises(ValidationError, match="final test split"):
        miner.validate_hard_negative_leakage(
            (test_split_negative,),
            pages=pages,
            queries=queries,
            final_test_split="test",
        )


def test_mining_pipeline_writes_split_safe_outputs_and_source_support(
    tmp_path: Path,
) -> None:
    miner = _miner_module()
    config_path = _write_temp_config(tmp_path, extra_sources={"unknown_source": True})

    result = miner.run_hard_negative_mining(
        miner.load_hard_negative_config(config_path),
        repo_root=Path.cwd(),
    )

    train_path = tmp_path / "train.jsonl"
    dev_path = tmp_path / "dev.jsonl"
    summary_path = tmp_path / "mining-summary.json"
    leakage_path = tmp_path / "leakage-check.json"
    run_card_path = tmp_path / "run-card.md"
    brief_path = tmp_path / "human-brief.html"
    ledger_path = tmp_path / "progress-ledger.yaml"

    assert result["outputs"]["train_jsonl"] == str(train_path)
    assert train_path.is_file()
    assert dev_path.is_file()
    assert summary_path.is_file()
    assert leakage_path.is_file()
    assert run_card_path.is_file()
    assert brief_path.is_file()

    train_records = miner.load_hard_negative_jsonl(train_path)
    dev_records = miner.load_hard_negative_jsonl(dev_path)
    assert train_records
    assert dev_records
    assert {record.split for record in train_records} == {"train"}
    assert {record.split for record in dev_records} == {"dev"}
    assert not any(record.query_id.startswith("manual-b") for record in train_records)
    assert not any(record.query_id.startswith("manual-c") for record in train_records)
    assert not any(record.query_id.startswith("manual-c") for record in dev_records)
    assert not any(
        record.negative_page_id.startswith("manual-c") for record in train_records
    )
    assert not any(
        record.negative_page_id.startswith("manual-c") for record in dev_records
    )
    assert all(
        record.negative_page_id != record.positive_page_id
        for record in (*train_records, *dev_records)
    )

    emitted_sources = {
        record.negative_source for record in (*train_records, *dev_records)
    }
    assert {
        "bm25",
        "lexical_cosine",
        "bm25_lexical_rrf",
        "mock_visual",
        "same_document",
        "tag_aware",
    } <= emitted_sources

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "hard_negative_mining_generated"
    assert summary["final_test_status"] == "not_run"
    assert summary["record_counts"]["negative_split_counts_by_query_split"] == {
        "dev": {"dev": 429},
        "train": {"train": 429},
    }
    assert summary["boundary"] == {
        "cpu_only": True,
        "network_required": False,
        "gpu_required": False,
        "model_download_required": False,
        "external_embeddings_used": False,
        "real_colpali_or_colqwen_execution": False,
        "training_run": False,
        "final_test_evaluated": False,
        "benchmark_claim": "none",
        "rag_or_chatbot_behavior": False,
    }
    for source in emitted_sources:
        assert summary["source_support"][source]["support"] > 0
    assert summary["source_support"]["unknown_source"] == {
        "status": "unsupported",
        "support": 0,
        "reason": "unsupported_negative_source",
        "evidence": None,
    }

    leakage = json.loads(leakage_path.read_text(encoding="utf-8"))
    assert leakage["status"] == "passed"
    assert leakage["checks"]["negative_not_positive"]["passed"] is True
    assert leakage["checks"]["train_has_no_dev_or_test_query_ids"]["passed"] is True
    assert leakage["checks"]["dev_has_no_test_query_ids"]["passed"] is True
    assert leakage["checks"]["test_split_absent_from_artifacts"]["passed"] is True
    same_split = leakage["checks"]["evaluated_split_pages_same_split_negatives"]
    assert same_split["passed"] is True
    assert same_split["negative_split_counts_by_query_split"] == {
        "dev": {"dev": 429},
        "train": {"train": 429},
    }

    run_card = run_card_path.read_text(encoding="utf-8")
    brief = brief_path.read_text(encoding="utf-8")
    assert "hard-negative mining" in run_card
    assert "no training" in run_card
    assert "final test evaluation: not_run" in run_card
    assert "结论" in brief
    assert "不训练" in brief

    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    hard_negative_status = ledger["hard_negative_mining_status"]
    assert hard_negative_status["status"] == "generated"
    assert hard_negative_status["final_test_evaluation"] == "not_run"
    assert hard_negative_status["training"] == "not_started"
    assert hard_negative_status["benchmark_claim"] == "none"


def test_cli_rejects_final_test_split_and_mvp_still_works(tmp_path: Path) -> None:
    invalid_config = _write_temp_config(tmp_path, evaluated_splits=("train", "test"))

    failed = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.mine_hard_negatives",
            "--config",
            str(invalid_config),
        ],
        cwd=Path.cwd(),
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert failed.returncode == 2
    assert "final_test_split must not be included" in failed.stderr

    valid_config = _write_temp_config(tmp_path / "valid")
    passed = subprocess.run(
        [
            sys.executable,
            "-m",
            "visdoc_retrieve.mine_hard_negatives",
            "--config",
            str(valid_config),
        ],
        cwd=Path.cwd(),
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert passed.returncode == 0
    assert (tmp_path / "valid" / "train.jsonl").is_file()
    assert (tmp_path / "valid" / "dev.jsonl").is_file()

    mvp_report = run_mvp_pipeline(
        load_mvp_config(Path("configs/mvp.json")),
        repo_root=Path.cwd(),
    )
    assert mvp_report["metrics"]["boundary"]["hard_negative_mining"] is False
    assert mvp_report["metrics"]["boundary"]["training_run"] is False
    assert mvp_report["metrics"]["final_test_status"] == "not_run"


def _miner_module() -> ModuleType:
    try:
        return importlib.import_module("visdoc_retrieve.hard_negatives")
    except ModuleNotFoundError as exc:
        if exc.name == "visdoc_retrieve.hard_negatives":
            pytest.fail(f"missing hard-negative miner module: {exc}")
        raise


def _write_temp_config(
    tmp_path: Path,
    *,
    evaluated_splits: tuple[str, ...] = ("train", "dev"),
    extra_sources: dict[str, bool] | None = None,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    ledger_path = tmp_path / "progress-ledger.yaml"
    shutil.copyfile(Path("reports/progress-ledger.yaml"), ledger_path)
    sources = {
        "bm25": True,
        "lexical_cosine": True,
        "bm25_lexical_rrf": True,
        "mock_visual": True,
        "same_document": True,
        "tag_aware": True,
    }
    if extra_sources:
        sources.update(extra_sources)
    config = {
        "name": "synthetic-smoke-hard-negatives-test",
        "pages_manifest": "data/synthetic-smoke/pages.jsonl",
        "queries_manifest": "data/synthetic-smoke/queries.jsonl",
        "evaluated_splits": list(evaluated_splits),
        "candidate_universe": "evaluated_split_pages",
        "final_test_split": "test",
        "top_k_per_source": 3,
        "sources": {
            source: {"enabled": enabled, "top_k": 3}
            for source, enabled in sources.items()
        },
        "outputs": {
            "train_jsonl": str(tmp_path / "train.jsonl"),
            "dev_jsonl": str(tmp_path / "dev.jsonl"),
            "summary": str(tmp_path / "mining-summary.json"),
            "leakage_check": str(tmp_path / "leakage-check.json"),
            "run_card": str(tmp_path / "run-card.md"),
            "human_brief": str(tmp_path / "human-brief.html"),
            "progress_ledger": str(ledger_path),
        },
    }
    config_path = tmp_path / "hard_negatives.json"
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return config_path
