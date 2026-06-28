"""Typed validators for Phase 1 retrieval data manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

VALID_SPLITS = frozenset({"train", "dev", "test"})
VALID_QUERY_TYPES = frozenset({"text", "table", "figure", "layout", "ocr_failure"})
PAGE_FIELDS = frozenset(
    {
        "page_id",
        "doc_id",
        "page_number",
        "image_path",
        "text_path",
        "family_id",
        "split",
        "content_hash",
    }
)
QUERY_FIELDS = frozenset(
    {
        "query_id",
        "query",
        "positive_page_ids",
        "family_id",
        "split",
        "query_type",
        "source",
    }
)


class ValidationError(ValueError):
    """Raised when a manifest record violates the Phase 1 data contract."""


@dataclass(frozen=True, slots=True)
class PageRecord:
    """Validated page manifest record."""

    page_id: str
    doc_id: str
    page_number: int
    image_path: str
    text_path: str
    family_id: str
    split: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class QuerySource:
    """Source metadata for a synthetic query."""

    doc_id: str
    page_id: str
    page_number: int
    description: str


@dataclass(frozen=True, slots=True)
class QueryRecord:
    """Validated query relevance manifest record."""

    query_id: str
    query: str
    positive_page_ids: tuple[str, ...]
    family_id: str
    split: str
    query_type: str
    source: QuerySource


def validate_page_record(record: Mapping[str, object]) -> PageRecord:
    """Validate and normalize one page manifest record."""

    _reject_unknown_fields(record, PAGE_FIELDS)

    content_hash = _required_str(record, "content_hash")
    is_sha256 = len(content_hash) == 64 and all(
        char in "0123456789abcdef" for char in content_hash
    )
    if not is_sha256:
        raise ValidationError(
            "content_hash must be a lowercase hexadecimal SHA-256 digest"
        )

    split = _required_str(record, "split")
    if split not in VALID_SPLITS:
        raise ValidationError(f"split must be one of {sorted(VALID_SPLITS)}")

    return PageRecord(
        page_id=_required_str(record, "page_id"),
        doc_id=_required_str(record, "doc_id"),
        page_number=_required_positive_int(record, "page_number"),
        image_path=_required_relative_path(record, "image_path"),
        text_path=_required_relative_path(record, "text_path"),
        family_id=_required_str(record, "family_id"),
        split=split,
        content_hash=content_hash,
    )


def validate_pages(
    records: Iterable[Mapping[str, object] | PageRecord],
) -> tuple[PageRecord, ...]:
    """Validate a page manifest and reject duplicate page IDs."""

    pages: list[PageRecord] = []
    seen: set[str] = set()
    for record in records:
        page = (
            record if isinstance(record, PageRecord) else validate_page_record(record)
        )
        if page.page_id in seen:
            raise ValidationError(f"duplicate page_id: {page.page_id}")
        seen.add(page.page_id)
        pages.append(page)
    return tuple(pages)


def validate_query_record(
    record: Mapping[str, object],
    *,
    pages_by_id: Mapping[str, PageRecord] | None = None,
) -> QueryRecord:
    """Validate and normalize one query relevance record."""

    _reject_unknown_fields(record, QUERY_FIELDS)

    split = _required_str(record, "split")
    if split not in VALID_SPLITS:
        raise ValidationError(f"split must be one of {sorted(VALID_SPLITS)}")

    query_type = _required_str(record, "query_type")
    if query_type not in VALID_QUERY_TYPES:
        raise ValidationError(f"query_type must be one of {sorted(VALID_QUERY_TYPES)}")

    family_id = _required_str(record, "family_id")
    positive_page_ids = _required_str_sequence(record, "positive_page_ids")
    if not positive_page_ids:
        raise ValidationError("positive_page_ids must contain at least one page_id")

    if pages_by_id is not None:
        for page_id in positive_page_ids:
            page = pages_by_id.get(page_id)
            if page is None:
                raise ValidationError(f"unknown positive page_id: {page_id}")
            if page.family_id != family_id:
                raise ValidationError("positive page must use the query family_id")
            if page.split != split:
                raise ValidationError("positive page must use the query split")

    source = _validate_query_source(_required_mapping(record, "source"))
    if source.page_id not in positive_page_ids:
        raise ValidationError("source page_id must be one of positive_page_ids")

    return QueryRecord(
        query_id=_required_str(record, "query_id"),
        query=_required_str(record, "query"),
        positive_page_ids=positive_page_ids,
        family_id=family_id,
        split=split,
        query_type=query_type,
        source=source,
    )


def validate_queries(
    records: Iterable[Mapping[str, object] | QueryRecord],
    pages: Iterable[Mapping[str, object] | PageRecord],
) -> tuple[QueryRecord, ...]:
    """Validate a query manifest against a page manifest."""

    page_records = validate_pages(pages)
    pages_by_id = {page.page_id: page for page in page_records}
    queries: list[QueryRecord] = []
    seen: set[str] = set()
    for record in records:
        query = (
            record
            if isinstance(record, QueryRecord)
            else validate_query_record(record, pages_by_id=pages_by_id)
        )
        if query.query_id in seen:
            raise ValidationError(f"duplicate query_id: {query.query_id}")
        seen.add(query.query_id)
        queries.append(query)
    return tuple(queries)


def validate_family_split_consistency(
    pages: Iterable[Mapping[str, object] | PageRecord],
    queries: Iterable[Mapping[str, object] | QueryRecord],
) -> None:
    """Validate that page/query splits stay consistent at family granularity."""

    page_records = validate_pages(pages)
    pages_by_id = {page.page_id: page for page in page_records}
    family_to_split: dict[str, str] = {}
    for page in page_records:
        previous_split = family_to_split.setdefault(page.family_id, page.split)
        if previous_split != page.split:
            raise ValidationError(f"family_id has multiple splits: {page.family_id}")

    for record in queries:
        query = (
            record
            if isinstance(record, QueryRecord)
            else validate_query_record(record, pages_by_id=pages_by_id)
        )
        family_split = family_to_split.get(query.family_id)
        if family_split is None:
            raise ValidationError(
                f"query references unknown family_id: {query.family_id}"
            )
        if query.split != family_split:
            raise ValidationError("query split must match its family split")
        for page_id in query.positive_page_ids:
            page = pages_by_id[page_id]
            if page.split != query.split:
                raise ValidationError(
                    "query positive page split must match query split"
                )
            if page.family_id != query.family_id:
                raise ValidationError(
                    "query positive page family must match query family"
                )


def validate_no_test_page_leakage(
    candidate_page_ids: Iterable[str],
    pages: Iterable[Mapping[str, object] | PageRecord],
    *,
    final_test_split: str = "test",
) -> None:
    """Reject candidate page IDs that would leak final test pages into training."""

    page_records = validate_pages(pages)
    pages_by_id = {page.page_id: page for page in page_records}
    for page_id in candidate_page_ids:
        if not isinstance(page_id, str) or not page_id.strip():
            raise ValidationError("candidate page IDs must be non-empty strings")
        page = pages_by_id.get(page_id)
        if page is None:
            raise ValidationError(f"unknown candidate page_id: {page_id}")
        if page.split == final_test_split:
            raise ValidationError(
                f"candidate page_id belongs to final test split: {page_id}"
            )


def load_jsonl(path: Path) -> list[dict[str, object]]:
    """Load a UTF-8 JSONL manifest file into JSON object records."""

    records: list[dict[str, object]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_number} must contain a JSON object")
        records.append(cast(dict[str, object], value))
    return records


def write_jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    """Write deterministic UTF-8 JSONL sorted by stable record ID."""

    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=_record_sort_key)
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in sorted_records
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_content_hash(image_path: Path, text_path: Path) -> str:
    """Hash generated page image bytes plus OCR-like text bytes."""

    digest = hashlib.sha256()
    digest.update(image_path.read_bytes())
    digest.update(b"\0")
    digest.update(text_path.read_bytes())
    return digest.hexdigest()


def _validate_query_source(record: Mapping[str, object]) -> QuerySource:
    return QuerySource(
        doc_id=_required_str(record, "doc_id"),
        page_id=_required_str(record, "page_id"),
        page_number=_required_positive_int(record, "page_number"),
        description=_required_str(record, "description"),
    )


def _required_mapping(record: Mapping[str, object], field: str) -> Mapping[str, object]:
    value = _required(record, field)
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field} must be an object")
    return value


def _required_str(record: Mapping[str, object], field: str) -> str:
    value = _required(record, field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value


def _required_positive_int(record: Mapping[str, object], field: str) -> int:
    value = _required(record, field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{field} must be a positive integer")
    return value


def _required_str_sequence(record: Mapping[str, object], field: str) -> tuple[str, ...]:
    value = _required(record, field)
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValidationError(f"{field} must be a list of non-empty strings")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field} must contain only non-empty strings")
        values.append(item)
    return tuple(values)


def _required_relative_path(record: Mapping[str, object], field: str) -> str:
    value = _required_str(record, field)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError(f"{field} must be a repo-relative path")
    return value


def _required(record: Mapping[str, object], field: str) -> object:
    if field not in record:
        raise ValidationError(f"missing required field: {field}")
    return record[field]


def _reject_unknown_fields(
    record: Mapping[str, object],
    allowed_fields: frozenset[str],
) -> None:
    unknown_fields = sorted(set(record) - allowed_fields)
    if unknown_fields:
        raise ValidationError(f"unexpected field: {unknown_fields[0]}")


def _record_sort_key(record: Mapping[str, object]) -> str:
    for key in ("page_id", "query_id", "family_id"):
        value = record.get(key)
        if isinstance(value, str):
            return value
    return json.dumps(cast(Any, record), ensure_ascii=False, sort_keys=True)
