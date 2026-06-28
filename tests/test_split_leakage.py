"""Tests for family split consistency and final-test leakage guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from visdoc_retrieve.data_schema import (
    PageRecord,
    QueryRecord,
    ValidationError,
    load_jsonl,
    validate_family_split_consistency,
    validate_no_test_page_leakage,
    validate_pages,
    validate_queries,
)
from visdoc_retrieve.synthetic_corpus import generate_default_corpus


def _load_generated_records(
    output_dir: Path,
) -> tuple[tuple[PageRecord, ...], tuple[QueryRecord, ...]]:
    pages = validate_pages(load_jsonl(output_dir / "pages.jsonl"))
    queries = validate_queries(load_jsonl(output_dir / "queries.jsonl"), pages)
    return pages, queries


def test_generated_corpus_uses_family_consistent_splits(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    generate_default_corpus(output_dir)
    pages, queries = _load_generated_records(output_dir)

    validate_family_split_consistency(pages, queries)
    split_to_families = {
        split: {page.family_id for page in pages if page.split == split}
        for split in ("train", "dev", "test")
    }

    assert split_to_families == {
        "train": {"manual-a"},
        "dev": {"manual-b"},
        "test": {"manual-c"},
    }


def test_family_split_consistency_rejects_query_positive_split_mismatch(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    generate_default_corpus(output_dir)
    pages = validate_pages(load_jsonl(output_dir / "pages.jsonl"))
    queries = load_jsonl(output_dir / "queries.jsonl")
    broken_query = dict(queries[0])
    broken_query["split"] = "test"

    with pytest.raises(ValidationError, match="split"):
        validate_family_split_consistency(pages, [broken_query])


def test_leakage_guard_rejects_training_candidates_from_final_test_split(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "data" / "synthetic-smoke"

    generate_default_corpus(output_dir)
    pages = validate_pages(load_jsonl(output_dir / "pages.jsonl"))
    non_test_candidates = [page.page_id for page in pages if page.split != "test"]
    test_page = next(page for page in pages if page.split == "test")

    validate_no_test_page_leakage(non_test_candidates, pages)

    with pytest.raises(ValidationError, match="test"):
        validate_no_test_page_leakage(
            [non_test_candidates[0], test_page.page_id],
            pages,
        )
