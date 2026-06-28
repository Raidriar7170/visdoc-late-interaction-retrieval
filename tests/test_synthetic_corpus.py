"""Tests for deterministic Phase 1 synthetic corpus generation."""

from __future__ import annotations

import json
from pathlib import Path

from visdoc_retrieve.data_schema import (
    load_jsonl,
    validate_pages,
    validate_queries,
)
from visdoc_retrieve.synthetic_corpus import generate_default_corpus

LOGICAL_ROOT = "data/synthetic-smoke"
QUERY_FIELDS = {
    "query_id",
    "query",
    "positive_page_ids",
    "family_id",
    "split",
    "query_type",
    "source",
}


def _artifact_path(output_dir: Path, logical_path: str) -> Path:
    assert logical_path.startswith(f"{LOGICAL_ROOT}/")
    return output_dir / logical_path.removeprefix(f"{LOGICAL_ROOT}/")


def test_default_corpus_generation_matches_phase_1_smoke_contract(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    summary = generate_default_corpus(output_dir)
    pages = validate_pages(load_jsonl(output_dir / "pages.jsonl"))
    queries = validate_queries(load_jsonl(output_dir / "queries.jsonl"), pages)

    assert summary["counts"] == {"families": 3, "pages": 24, "queries": 72}
    assert len({page.family_id for page in pages}) == 3
    assert len(pages) == 24
    assert len(queries) == 72
    assert {query.query_type for query in queries} >= {
        "text",
        "table",
        "figure",
        "layout",
        "ocr_failure",
    }


def test_generated_page_manifest_points_to_existing_artifacts(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    generate_default_corpus(output_dir)
    pages = validate_pages(load_jsonl(output_dir / "pages.jsonl"))

    for page in pages:
        assert _artifact_path(output_dir, page.image_path).is_file()
        assert _artifact_path(output_dir, page.text_path).is_file()


def test_generated_query_manifest_uses_only_schema_fields(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    generate_default_corpus(output_dir)
    query_records = load_jsonl(output_dir / "queries.jsonl")

    assert query_records
    assert all(set(record) == QUERY_FIELDS for record in query_records)


def test_repeated_default_generation_is_byte_stable(tmp_path: Path) -> None:
    output_a = tmp_path / "run-a" / "data" / "synthetic-smoke"
    output_b = tmp_path / "run-b" / "data" / "synthetic-smoke"

    summary_a = generate_default_corpus(output_a)
    summary_b = generate_default_corpus(output_b)
    pages_a = validate_pages(load_jsonl(output_a / "pages.jsonl"))
    pages_b = validate_pages(load_jsonl(output_b / "pages.jsonl"))

    assert summary_a == summary_b
    assert (output_a / "pages.jsonl").read_bytes() == (
        output_b / "pages.jsonl"
    ).read_bytes()
    assert (output_a / "queries.jsonl").read_bytes() == (
        output_b / "queries.jsonl"
    ).read_bytes()
    assert [page.content_hash for page in pages_a] == [
        page.content_hash for page in pages_b
    ]


def test_summary_contains_no_retrieval_or_benchmark_metrics(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    summary = generate_default_corpus(output_dir)
    summary_text = json.dumps(summary, sort_keys=True).lower()

    for forbidden in ("recall", "mrr", "ndcg", "ranking", "score", "benchmark"):
        assert forbidden not in summary_text
