"""Tests for Phase 1 page and query manifest validation."""

from __future__ import annotations

import pytest

from visdoc_retrieve.data_schema import (
    ValidationError,
    validate_page_record,
    validate_pages,
    validate_queries,
    validate_query_record,
)

VALID_HASH = "a" * 64


def _page_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "page_id": "manual-a-p01",
        "doc_id": "manual-a",
        "page_number": 1,
        "image_path": "data/synthetic-smoke/pages/manual-a/p01.png",
        "text_path": "data/synthetic-smoke/text/manual-a/p01.txt",
        "family_id": "manual-a",
        "split": "train",
        "content_hash": VALID_HASH,
    }
    record.update(overrides)
    return record


def _query_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "query_id": "manual-a-p01-q01",
        "query": "Which pressure limit appears in the pump table?",
        "positive_page_ids": ["manual-a-p01"],
        "family_id": "manual-a",
        "split": "train",
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


def test_page_manifest_record_validation_accepts_required_fields() -> None:
    page = validate_page_record(_page_record())

    assert page.page_id == "manual-a-p01"
    assert page.page_number == 1
    assert page.image_path == "data/synthetic-smoke/pages/manual-a/p01.png"


def test_page_manifest_validation_rejects_missing_fields_and_bad_split() -> None:
    missing_hash = _page_record()
    del missing_hash["content_hash"]

    with pytest.raises(ValidationError, match="content_hash"):
        validate_page_record(missing_hash)

    with pytest.raises(ValidationError, match="split"):
        validate_page_record(_page_record(split="holdout"))


def test_page_manifest_validation_rejects_unknown_top_level_fields() -> None:
    with pytest.raises(ValidationError, match="unexpected field"):
        validate_page_record(_page_record(extra_path="data/synthetic-smoke/extra.txt"))


def test_query_manifest_validation_accepts_known_positive_page() -> None:
    pages = validate_pages([_page_record()])
    query = validate_query_record(
        _query_record(),
        pages_by_id={page.page_id: page for page in pages},
    )

    assert query.positive_page_ids == ("manual-a-p01",)
    assert query.source.description == "synthetic table caption"


def test_query_manifest_validation_rejects_invalid_type_and_unknown_positive() -> None:
    pages = validate_pages([_page_record()])
    pages_by_id = {page.page_id: page for page in pages}

    with pytest.raises(ValidationError, match="query_type"):
        validate_query_record(
            _query_record(query_type="diagram"),
            pages_by_id=pages_by_id,
        )

    with pytest.raises(ValidationError, match="unknown"):
        validate_query_record(
            _query_record(positive_page_ids=["missing-p01"]),
            pages_by_id=pages_by_id,
        )


def test_query_manifest_validation_rejects_unknown_top_level_fields() -> None:
    pages = validate_pages([_page_record()])

    with pytest.raises(ValidationError, match="artifact_hint"):
        validate_query_record(
            _query_record(artifact_hint="data/synthetic-smoke/text/manual-a/p01.txt"),
            pages_by_id={page.page_id: page for page in pages},
        )


def test_query_manifest_validation_rejects_positive_page_split_mismatch() -> None:
    pages = validate_pages([_page_record(split="dev")])

    with pytest.raises(ValidationError, match="split"):
        validate_queries([_query_record(split="train")], pages)
