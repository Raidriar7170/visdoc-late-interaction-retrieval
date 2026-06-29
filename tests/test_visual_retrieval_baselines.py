"""Tests for deterministic visual smoke retrieval baselines."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from visdoc_retrieve.data_schema import ValidationError, write_jsonl
from visdoc_retrieve.visual_baseline_report import (
    load_visual_report_config,
    run_visual_baseline_report,
)
from visdoc_retrieve.visual_retrieval import (
    VisualPage,
    VisualSmokeRetriever,
    load_visual_corpus,
)


def test_visual_corpus_loader_loads_image_bytes_without_text_artifacts(
    tmp_path: Path,
) -> None:
    page_image = tmp_path / "page-a.png"
    page_image.write_bytes(b"alpha pump visual bytes")
    missing_text = tmp_path / "missing.txt"
    pages_path = tmp_path / "pages.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    write_jsonl(
        pages_path,
        [
            _page_record(
                image_path=page_image.name,
                text_path=missing_text.name,
            )
        ],
    )
    write_jsonl(queries_path, [_query_record()])

    corpus = load_visual_corpus(
        repo_root=tmp_path,
        pages_manifest=pages_path,
        queries_manifest=queries_path,
    )

    page = corpus.pages_by_id["manual-a-p01"]
    assert page.image_bytes == b"alpha pump visual bytes"
    assert page.split == "dev"
    assert page.text_path == missing_text.name
    assert corpus.queries_by_id["manual-a-p01-q01"].positive_page_ids == (
        "manual-a-p01",
    )


def test_visual_corpus_loader_fails_fast_on_missing_image_artifact(
    tmp_path: Path,
) -> None:
    pages_path = tmp_path / "pages.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    write_jsonl(
        pages_path,
        [_page_record(image_path="missing.png")],
    )
    write_jsonl(queries_path, [_query_record()])

    with pytest.raises(ValidationError, match="missing image artifact"):
        load_visual_corpus(
            repo_root=tmp_path,
            pages_manifest=pages_path,
            queries_manifest=queries_path,
        )


def test_visual_smoke_retriever_is_local_deterministic_and_tie_stable() -> None:
    pages = (
        VisualPage("page-b", "dev", "family", b"alpha pump panel"),
        VisualPage("page-a", "dev", "family", b"alpha pump panel"),
        VisualPage("page-c", "dev", "family", b"unrelated optical switch"),
    )
    retriever = VisualSmokeRetriever(pages)

    first = retriever.rank("alpha pump")
    second = retriever.rank("alpha pump")

    assert [item.page_id for item in first] == ["page-a", "page-b", "page-c"]
    assert [(item.page_id, item.score) for item in first] == [
        (item.page_id, item.score) for item in second
    ]
    assert retriever.uses_external_model is False
    assert retriever.gpu_required is False


def test_visual_report_runner_generates_diagnostic_smoke_report(
    tmp_path: Path,
) -> None:
    config = load_visual_report_config(
        Path("configs/visual-baselines-synthetic-smoke.json")
    )
    output_path = tmp_path / "visual-baselines-report.json"

    report = run_visual_baseline_report(
        config,
        repo_root=Path.cwd(),
        output_path=output_path,
    )
    persisted = json.loads(output_path.read_text(encoding="utf-8"))

    assert persisted == report
    assert report["status"] == "diagnostic_only"
    assert report["visual_retriever_status"] == "deterministic_local_smoke"
    assert report["final_test_status"] == "not_run"
    assert report["evaluated_splits"] == ["dev"]
    assert sorted(report["methods"]) == ["visual_smoke"]

    method = report["methods"]["visual_smoke"]
    assert method["metrics"]["evaluated_queries"] == 24
    assert method["diagnostics"]["index_size_pages"]["value"] == 8
    assert method["diagnostics"]["patch_tokens_per_page"]["min"] > 0
    assert method["hard_negative_hit_rate"] == {
        "status": "not_available",
        "support": 0,
    }

    boundary = report["boundary"]
    assert boundary["page_text_artifacts_read"] is False
    assert boundary["network_required"] is False
    assert boundary["gpu_required"] is False
    assert boundary["external_model_download_required"] is False
    assert boundary["colpali_or_colqwen_inference"] is False
    assert boundary["hard_negative_triples_emitted"] is False
    assert boundary["training_run"] is False
    assert boundary["final_test_evaluated"] is False
    assert boundary["benchmark_claim"] == "none"


def _page_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "page_id": "manual-a-p01",
        "doc_id": "manual-a",
        "page_number": 1,
        "image_path": "data/synthetic-smoke/pages/manual-a/p01.png",
        "text_path": "data/synthetic-smoke/text/manual-a/p01.txt",
        "family_id": "manual-a",
        "split": "dev",
        "content_hash": "a" * 64,
    }
    record.update(overrides)
    return record


def _query_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "query_id": "manual-a-p01-q01",
        "query": "Which pressure limit appears in the pump table?",
        "positive_page_ids": ["manual-a-p01"],
        "family_id": "manual-a",
        "split": "dev",
        "query_type": "table",
        "source": {
            "doc_id": "manual-a",
            "page_id": "manual-a-p01",
            "page_number": 1,
            "description": "synthetic table caption",
        },
    }
    record.update(overrides)
    return record
