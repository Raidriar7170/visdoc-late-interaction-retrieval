"""Deterministic hard-negative mining for train/dev smoke artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from visdoc_retrieve.data_schema import (
    PageRecord,
    QueryRecord,
    ValidationError,
    load_jsonl,
    validate_family_split_consistency,
    validate_pages,
    validate_queries,
)
from visdoc_retrieve.text_retrieval import (
    BM25LexicalRrfRetriever,
    BM25Retriever,
    LexicalCosineRetriever,
    TextPage,
    TextQuery,
    load_text_corpus,
)
from visdoc_retrieve.text_retrieval import (
    RankingItem as TextRankingItem,
)
from visdoc_retrieve.visual_retrieval import (
    MockVisualRetriever,
    VisualPage,
    VisualQuery,
    load_visual_corpus,
)
from visdoc_retrieve.visual_retrieval import (
    RankingItem as VisualRankingItem,
)

HARD_NEGATIVE_COMMAND = (
    "PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives "
    "--config configs/hard_negatives.json"
)
SUPPORTED_SOURCES = frozenset(
    {
        "bm25",
        "lexical_cosine",
        "local_tfidf_cosine",
        "bm25_lexical_rrf",
        "hybrid_rrf",
        "mock_visual",
        "same_document",
        "tag_aware",
    }
)


class _TextRanker(Protocol):
    """Text ranker shape used by hard-negative source generation."""

    def rank(self, query: str) -> tuple[TextRankingItem, ...]:
        """Rank pages for a query string."""


@dataclass(frozen=True, slots=True)
class HardNegativeRecord:
    """One mined hard-negative triple candidate."""

    query_id: str
    positive_page_id: str
    negative_page_id: str
    split: str
    negative_source: str
    rank: int
    score: float | None
    candidate_universe_id: str
    reason: str
    evidence: Mapping[str, object]

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON object for this record."""

        return {
            "candidate_universe_id": self.candidate_universe_id,
            "evidence": dict(self.evidence),
            "negative_page_id": self.negative_page_id,
            "negative_source": self.negative_source,
            "positive_page_id": self.positive_page_id,
            "query_id": self.query_id,
            "rank": self.rank,
            "reason": self.reason,
            "score": self.score,
            "split": self.split,
        }


@dataclass(frozen=True, slots=True)
class SourceConfig:
    """Configuration for one negative source."""

    enabled: bool
    top_k: int


@dataclass(frozen=True, slots=True)
class HardNegativeOutputs:
    """Output paths for one mining run."""

    train_jsonl: Path
    dev_jsonl: Path
    summary: Path
    leakage_check: Path
    run_card: Path
    human_brief: Path
    progress_ledger: Path


@dataclass(frozen=True, slots=True)
class HardNegativeConfig:
    """Config for deterministic hard-negative mining."""

    name: str
    pages_manifest: Path
    queries_manifest: Path
    evaluated_splits: tuple[str, ...]
    candidate_universe: str
    final_test_split: str
    top_k_per_source: int
    sources: Mapping[str, SourceConfig]
    outputs: HardNegativeOutputs
    config_path: Path | None


def load_hard_negative_config(path: Path) -> HardNegativeConfig:
    """Load a JSON hard-negative mining config."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("hard-negative config must be a JSON object")
    evaluated_splits = _required_str_tuple(data, "evaluated_splits")
    final_test_split = _required_str(data, "final_test_split")
    if final_test_split in evaluated_splits:
        raise ValueError("final_test_split must not be included in evaluated_splits")
    top_k_per_source = _positive_int(
        data.get("top_k_per_source", 3),
        "top_k_per_source",
    )
    outputs = _required_mapping(data, "outputs")
    return HardNegativeConfig(
        name=_required_str(data, "name"),
        pages_manifest=Path(_required_str(data, "pages_manifest")),
        queries_manifest=Path(_required_str(data, "queries_manifest")),
        evaluated_splits=evaluated_splits,
        candidate_universe=_required_str(data, "candidate_universe"),
        final_test_split=final_test_split,
        top_k_per_source=top_k_per_source,
        sources=_source_configs(
            _required_mapping(data, "sources"),
            default_top_k=top_k_per_source,
        ),
        outputs=HardNegativeOutputs(
            train_jsonl=Path(_required_str(outputs, "train_jsonl")),
            dev_jsonl=Path(_required_str(outputs, "dev_jsonl")),
            summary=Path(_required_str(outputs, "summary")),
            leakage_check=Path(_required_str(outputs, "leakage_check")),
            run_card=Path(_required_str(outputs, "run_card")),
            human_brief=Path(_required_str(outputs, "human_brief")),
            progress_ledger=Path(_required_str(outputs, "progress_ledger")),
        ),
        config_path=path,
    )


def run_hard_negative_mining(
    config: HardNegativeConfig,
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Run deterministic hard-negative mining and persist configured artifacts."""

    if config.final_test_split in config.evaluated_splits:
        raise ValueError("final_test_split must not be included in evaluated_splits")

    pages_path = _resolve_path(repo_root, config.pages_manifest)
    queries_path = _resolve_path(repo_root, config.queries_manifest)
    page_records = validate_pages(load_jsonl(pages_path))
    query_records = validate_queries(load_jsonl(queries_path), page_records)
    validate_family_split_consistency(page_records, query_records)

    text_corpus = load_text_corpus(
        repo_root=repo_root,
        pages_manifest=config.pages_manifest,
        queries_manifest=config.queries_manifest,
    )
    visual_corpus = load_visual_corpus(
        repo_root=repo_root,
        pages_manifest=config.pages_manifest,
        queries_manifest=config.queries_manifest,
    )

    records: list[HardNegativeRecord] = []
    source_support: dict[str, dict[str, object]] = {}
    for source_id in sorted(config.sources):
        source = config.sources[source_id]
        if not source.enabled:
            source_support[source_id] = {
                "status": "disabled",
                "support": 0,
                "reason": "source_disabled",
                "evidence": None,
            }
            continue
        if source_id not in SUPPORTED_SOURCES:
            source_support[source_id] = {
                "status": "unsupported",
                "support": 0,
                "reason": "unsupported_negative_source",
                "evidence": None,
            }
            continue
        source_records = _records_for_source(
            source_id=source_id,
            source=source,
            config=config,
            text_pages=text_corpus.pages,
            text_queries=text_corpus.queries,
            visual_pages=visual_corpus.pages,
            visual_queries=visual_corpus.queries,
            page_records=page_records,
            query_records=query_records,
        )
        records.extend(source_records)
        source_support[source_id] = _source_support_report(source_id, source_records)

    ordered_records = dedupe_and_sort_hard_negatives(records)
    validate_hard_negative_leakage(
        ordered_records,
        pages=page_records,
        queries=query_records,
        final_test_split=config.final_test_split,
    )

    train_records = tuple(
        record for record in ordered_records if record.split == "train"
    )
    dev_records = tuple(record for record in ordered_records if record.split == "dev")
    outputs = _resolved_outputs(repo_root, config.outputs)
    write_hard_negative_jsonl(outputs.train_jsonl, train_records)
    write_hard_negative_jsonl(outputs.dev_jsonl, dev_records)

    leakage_report = _build_leakage_report(
        ordered_records,
        pages=page_records,
        queries=query_records,
        final_test_split=config.final_test_split,
    )
    summary = _summary_report(
        config=config,
        records=ordered_records,
        train_records=train_records,
        dev_records=dev_records,
        source_support=source_support,
        outputs=outputs,
        repo_root=repo_root,
    )
    _write_json(outputs.summary, summary)
    _write_json(outputs.leakage_check, leakage_report)
    _write_run_card(outputs.run_card, summary)
    _write_human_brief(outputs.human_brief, summary)
    _update_progress_ledger(outputs.progress_ledger, summary)
    return {
        "status": "hard_negative_mining_generated",
        "outputs": cast(dict[str, object], summary["outputs"]),
        "summary": summary,
        "leakage": leakage_report,
    }


def dedupe_and_sort_hard_negatives(
    records: Iterable[HardNegativeRecord],
) -> tuple[HardNegativeRecord, ...]:
    """Remove duplicate query/source/negative records and return stable ordering."""

    best_by_key: dict[tuple[str, str, str, str, str], HardNegativeRecord] = {}
    for record in records:
        _validate_record(record)
        key = (
            record.split,
            record.query_id,
            record.positive_page_id,
            record.negative_source,
            record.negative_page_id,
        )
        previous = best_by_key.get(key)
        if previous is None or _dedupe_preference(record) < _dedupe_preference(
            previous
        ):
            best_by_key[key] = record
    return tuple(sorted(best_by_key.values(), key=_record_sort_key))


def write_hard_negative_jsonl(
    path: Path,
    records: Iterable[HardNegativeRecord],
) -> None:
    """Write hard-negative records as deterministic JSONL."""

    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = dedupe_and_sort_hard_negatives(records)
    lines = [
        json.dumps(
            record.to_json(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for record in ordered
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_hard_negative_jsonl(path: Path) -> tuple[HardNegativeRecord, ...]:
    """Load and validate hard-negative records from JSONL."""

    return tuple(_record_from_mapping(record) for record in load_jsonl(path))


def validate_hard_negative_leakage(
    records: Iterable[HardNegativeRecord],
    *,
    pages: Iterable[Mapping[str, object] | PageRecord],
    queries: Iterable[Mapping[str, object] | QueryRecord],
    final_test_split: str,
) -> None:
    """Raise when hard-negative records leak positives or final-test data."""

    page_records = validate_pages(pages)
    query_records = validate_queries(queries, page_records)
    pages_by_id = {page.page_id: page for page in page_records}
    queries_by_id = {query.query_id: query for query in query_records}
    seen_keys: set[tuple[str, str, str, str, str]] = set()

    for record in records:
        _validate_record(record)
        key = (
            record.split,
            record.query_id,
            record.positive_page_id,
            record.negative_source,
            record.negative_page_id,
        )
        if key in seen_keys:
            raise ValidationError("duplicate hard-negative record")
        seen_keys.add(key)

        query = queries_by_id.get(record.query_id)
        if query is None:
            raise ValidationError(
                f"unknown query_id in hard negatives: {record.query_id}"
            )
        if query.split != record.split:
            raise ValidationError("hard-negative split must match query split")
        if record.split == final_test_split:
            raise ValidationError("final test split must not appear in artifacts")
        if record.positive_page_id not in query.positive_page_ids:
            raise ValidationError("positive_page_id must be a query positive")
        if record.negative_page_id in query.positive_page_ids:
            raise ValidationError("negative_page_id must not equal a query positive")

        negative_page = pages_by_id.get(record.negative_page_id)
        if negative_page is None:
            raise ValidationError(
                f"unknown negative_page_id in hard negatives: {record.negative_page_id}"
            )
        if negative_page.split == final_test_split:
            raise ValidationError("negative_page_id belongs to final test split")
        if (
            record.candidate_universe_id == "evaluated_split_pages"
            and negative_page.split != record.split
        ):
            raise ValidationError(
                "evaluated_split_pages negatives must stay within query split"
            )


def _records_for_source(
    *,
    source_id: str,
    source: SourceConfig,
    config: HardNegativeConfig,
    text_pages: Sequence[TextPage],
    text_queries: Sequence[TextQuery],
    visual_pages: Sequence[VisualPage],
    visual_queries: Sequence[VisualQuery],
    page_records: Sequence[PageRecord],
    query_records: Sequence[QueryRecord],
) -> tuple[HardNegativeRecord, ...]:
    if source_id in {
        "bm25",
        "lexical_cosine",
        "local_tfidf_cosine",
        "bm25_lexical_rrf",
        "hybrid_rrf",
    }:
        return _text_source_records(
            source_id=source_id,
            source=source,
            config=config,
            pages=text_pages,
            queries=text_queries,
        )
    if source_id == "mock_visual":
        return _visual_source_records(
            source=source,
            config=config,
            pages=visual_pages,
            queries=visual_queries,
        )
    if source_id == "same_document":
        return _same_document_records(
            source=source,
            config=config,
            pages=page_records,
            queries=query_records,
        )
    if source_id == "tag_aware":
        return _tag_aware_records(
            source=source,
            config=config,
            pages=page_records,
            queries=query_records,
        )
    return ()


def _text_source_records(
    *,
    source_id: str,
    source: SourceConfig,
    config: HardNegativeConfig,
    pages: Sequence[TextPage],
    queries: Sequence[TextQuery],
) -> tuple[HardNegativeRecord, ...]:
    records: list[HardNegativeRecord] = []
    for split in config.evaluated_splits:
        split_pages = _candidate_text_pages(pages, split=split, config=config)
        split_queries = tuple(query for query in queries if query.split == split)
        retriever: _TextRanker
        if source_id == "bm25":
            retriever = BM25Retriever(split_pages)
            ranker_name = "bm25"
        elif source_id in {"lexical_cosine", "local_tfidf_cosine"}:
            retriever = LexicalCosineRetriever(split_pages)
            ranker_name = "lexical_cosine"
        else:
            retriever = BM25LexicalRrfRetriever(split_pages)
            ranker_name = "bm25_lexical_rrf"
        for query in sorted(split_queries, key=lambda item: item.query_id):
            records.extend(
                _records_from_ranking(
                    query_id=query.query_id,
                    query_text=query.query,
                    split=query.split,
                    positive_page_ids=query.positive_page_ids,
                    negative_source=source_id,
                    candidate_universe_id=config.candidate_universe,
                    rankings=retriever.rank(query.query),
                    top_k=source.top_k,
                    reason="ranked_wrong_page",
                    evidence_base={
                        "method": ranker_name,
                        "query_type": query.query_type,
                    },
                )
            )
    return tuple(records)


def _visual_source_records(
    *,
    source: SourceConfig,
    config: HardNegativeConfig,
    pages: Sequence[VisualPage],
    queries: Sequence[VisualQuery],
) -> tuple[HardNegativeRecord, ...]:
    records: list[HardNegativeRecord] = []
    for split in config.evaluated_splits:
        split_pages = _candidate_visual_pages(pages, split=split, config=config)
        split_queries = tuple(query for query in queries if query.split == split)
        retriever = MockVisualRetriever(split_pages)
        for query in sorted(split_queries, key=lambda item: item.query_id):
            records.extend(
                _records_from_ranking(
                    query_id=query.query_id,
                    query_text=query.query,
                    split=query.split,
                    positive_page_ids=query.positive_page_ids,
                    negative_source="mock_visual",
                    candidate_universe_id=config.candidate_universe,
                    rankings=retriever.rank(query),
                    top_k=source.top_k,
                    reason="mock_visual_maxsim_wrong_page",
                    evidence_base={
                        "method": "mock_visual",
                        "provider": "deterministic_mock",
                        "scoring": "maxsim",
                        "query_type": query.query_type,
                    },
                )
            )
    return tuple(records)


def _records_from_ranking(
    *,
    query_id: str,
    query_text: str,
    split: str,
    positive_page_ids: Sequence[str],
    negative_source: str,
    candidate_universe_id: str,
    rankings: Sequence[TextRankingItem | VisualRankingItem],
    top_k: int,
    reason: str,
    evidence_base: Mapping[str, object],
) -> list[HardNegativeRecord]:
    del query_text
    positives = set(positive_page_ids)
    records: list[HardNegativeRecord] = []
    wrong_count = 0
    for raw_rank, item in enumerate(rankings, start=1):
        if item.page_id in positives:
            continue
        wrong_count += 1
        if wrong_count > top_k:
            break
        for positive_page_id in sorted(positive_page_ids):
            evidence = {
                **dict(evidence_base),
                "raw_rank": raw_rank,
                "top_k_wrong_index": wrong_count,
            }
            records.append(
                HardNegativeRecord(
                    query_id=query_id,
                    positive_page_id=positive_page_id,
                    negative_page_id=item.page_id,
                    split=split,
                    negative_source=negative_source,
                    rank=raw_rank,
                    score=item.score,
                    candidate_universe_id=candidate_universe_id,
                    reason=reason,
                    evidence=evidence,
                )
            )
    return records


def _same_document_records(
    *,
    source: SourceConfig,
    config: HardNegativeConfig,
    pages: Sequence[PageRecord],
    queries: Sequence[QueryRecord],
) -> tuple[HardNegativeRecord, ...]:
    records: list[HardNegativeRecord] = []
    for query in _eligible_query_records(queries, config):
        candidates = [
            page
            for page in _candidate_page_records(pages, split=query.split, config=config)
            if page.doc_id == query.source.doc_id
            and page.page_id not in set(query.positive_page_ids)
        ]
        for rank, page in enumerate(
            sorted(candidates, key=lambda item: (item.page_number, item.page_id))[
                : source.top_k
            ],
            start=1,
        ):
            for positive_page_id in sorted(query.positive_page_ids):
                records.append(
                    HardNegativeRecord(
                        query_id=query.query_id,
                        positive_page_id=positive_page_id,
                        negative_page_id=page.page_id,
                        split=query.split,
                        negative_source="same_document",
                        rank=rank,
                        score=None,
                        candidate_universe_id=config.candidate_universe,
                        reason="same_document_wrong_page",
                        evidence={
                            "doc_id": page.doc_id,
                            "query_source_page_id": query.source.page_id,
                            "negative_page_number": page.page_number,
                        },
                    )
                )
    return tuple(records)


def _tag_aware_records(
    *,
    source: SourceConfig,
    config: HardNegativeConfig,
    pages: Sequence[PageRecord],
    queries: Sequence[QueryRecord],
) -> tuple[HardNegativeRecord, ...]:
    tags_by_page = _tags_by_positive_page(queries)
    records: list[HardNegativeRecord] = []
    for query in _eligible_query_records(queries, config):
        candidates = [
            page
            for page in _candidate_page_records(pages, split=query.split, config=config)
            if query.query_type in tags_by_page.get(page.page_id, set())
            and page.page_id not in set(query.positive_page_ids)
        ]
        for rank, page in enumerate(
            sorted(candidates, key=lambda item: (item.page_number, item.page_id))[
                : source.top_k
            ],
            start=1,
        ):
            for positive_page_id in sorted(query.positive_page_ids):
                records.append(
                    HardNegativeRecord(
                        query_id=query.query_id,
                        positive_page_id=positive_page_id,
                        negative_page_id=page.page_id,
                        split=query.split,
                        negative_source="tag_aware",
                        rank=rank,
                        score=None,
                        candidate_universe_id=config.candidate_universe,
                        reason="same_query_type_wrong_page",
                        evidence={
                            "query_type": query.query_type,
                            "negative_page_tags": sorted(tags_by_page[page.page_id]),
                        },
                    )
                )
    return tuple(records)


def _candidate_text_pages(
    pages: Sequence[TextPage],
    *,
    split: str,
    config: HardNegativeConfig,
) -> tuple[TextPage, ...]:
    if config.candidate_universe == "evaluated_split_pages":
        selected = [page for page in pages if page.split == split]
    elif config.candidate_universe == "non_train_pages":
        selected = [
            page
            for page in pages
            if page.split != "train" and page.split != config.final_test_split
        ]
    elif config.candidate_universe == "all_pages":
        selected = [page for page in pages if page.split != config.final_test_split]
    else:
        raise ValueError(f"unknown candidate_universe: {config.candidate_universe}")
    return tuple(sorted(selected, key=lambda item: item.page_id))


def _candidate_visual_pages(
    pages: Sequence[VisualPage],
    *,
    split: str,
    config: HardNegativeConfig,
) -> tuple[VisualPage, ...]:
    if config.candidate_universe == "evaluated_split_pages":
        selected = [page for page in pages if page.split == split]
    elif config.candidate_universe == "non_train_pages":
        selected = [
            page
            for page in pages
            if page.split != "train" and page.split != config.final_test_split
        ]
    elif config.candidate_universe == "all_pages":
        selected = [page for page in pages if page.split != config.final_test_split]
    else:
        raise ValueError(f"unknown candidate_universe: {config.candidate_universe}")
    return tuple(sorted(selected, key=lambda item: item.page_id))


def _candidate_page_records(
    pages: Sequence[PageRecord],
    *,
    split: str,
    config: HardNegativeConfig,
) -> tuple[PageRecord, ...]:
    if config.candidate_universe == "evaluated_split_pages":
        selected = [page for page in pages if page.split == split]
    elif config.candidate_universe == "non_train_pages":
        selected = [
            page
            for page in pages
            if page.split != "train" and page.split != config.final_test_split
        ]
    elif config.candidate_universe == "all_pages":
        selected = [page for page in pages if page.split != config.final_test_split]
    else:
        raise ValueError(f"unknown candidate_universe: {config.candidate_universe}")
    return tuple(sorted(selected, key=lambda item: item.page_id))


def _eligible_query_records(
    queries: Sequence[QueryRecord],
    config: HardNegativeConfig,
) -> tuple[QueryRecord, ...]:
    return tuple(
        sorted(
            (query for query in queries if query.split in set(config.evaluated_splits)),
            key=lambda item: item.query_id,
        )
    )


def _tags_by_positive_page(
    queries: Sequence[QueryRecord],
) -> dict[str, set[str]]:
    tags: dict[str, set[str]] = {}
    for query in queries:
        for page_id in query.positive_page_ids:
            tags.setdefault(page_id, set()).add(query.query_type)
    return tags


def _build_leakage_report(
    records: Sequence[HardNegativeRecord],
    *,
    pages: Sequence[PageRecord],
    queries: Sequence[QueryRecord],
    final_test_split: str,
) -> dict[str, object]:
    validate_hard_negative_leakage(
        records,
        pages=pages,
        queries=queries,
        final_test_split=final_test_split,
    )
    split_boundary = _split_boundary_report(records, pages)
    return {
        "status": "passed",
        "final_test_status": "not_run",
        "checks": {
            "negative_not_positive": {"passed": True, "violations": 0},
            "train_has_no_dev_or_test_query_ids": {"passed": True, "violations": 0},
            "dev_has_no_test_query_ids": {"passed": True, "violations": 0},
            "test_split_absent_from_artifacts": {"passed": True, "violations": 0},
            "evaluated_split_pages_same_split_negatives": split_boundary,
            "deterministic_dedupe_and_ordering": {"passed": True, "violations": 0},
        },
        "record_count": len(records),
    }


def _split_boundary_report(
    records: Sequence[HardNegativeRecord],
    pages: Sequence[PageRecord],
) -> dict[str, object]:
    pages_by_id = {page.page_id: page for page in pages}
    split_counts: dict[str, dict[str, int]] = {}
    for record in records:
        negative_split = pages_by_id[record.negative_page_id].split
        split_counts.setdefault(record.split, {})
        split_counts[record.split][negative_split] = (
            split_counts[record.split].get(negative_split, 0) + 1
        )
    return {
        "passed": all(
            record.split == pages_by_id[record.negative_page_id].split
            for record in records
            if record.candidate_universe_id == "evaluated_split_pages"
        ),
        "violations": 0,
        "negative_split_counts_by_query_split": {
            split: dict(sorted(counts.items()))
            for split, counts in sorted(split_counts.items())
        },
    }


def _summary_report(
    *,
    config: HardNegativeConfig,
    records: Sequence[HardNegativeRecord],
    train_records: Sequence[HardNegativeRecord],
    dev_records: Sequence[HardNegativeRecord],
    source_support: Mapping[str, Mapping[str, object]],
    outputs: HardNegativeOutputs,
    repo_root: Path,
) -> dict[str, object]:
    split_counts: dict[str, int] = {}
    for record in records:
        split_counts[record.split] = split_counts.get(record.split, 0) + 1
    return {
        "name": config.name,
        "status": "hard_negative_mining_generated",
        "command": HARD_NEGATIVE_COMMAND,
        "config": str(config.config_path) if config.config_path else None,
        "inputs": {
            "pages_manifest": str(config.pages_manifest),
            "queries_manifest": str(config.queries_manifest),
        },
        "evaluated_splits": list(config.evaluated_splits),
        "candidate_universe": {
            "id": config.candidate_universe,
            "final_test_split": config.final_test_split,
        },
        "record_counts": {
            "total": len(records),
            "train": len(train_records),
            "dev": len(dev_records),
            "by_split": dict(sorted(split_counts.items())),
            "negative_split_counts_by_query_split": _negative_split_counts(
                records,
                repo_root=repo_root,
                config=config,
            ),
        },
        "source_support": {
            source_id: dict(source_report)
            for source_id, source_report in sorted(source_support.items())
        },
        "final_test_status": "not_run",
        "boundary": {
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
        },
        "outputs": {
            "train_jsonl": _display_path(outputs.train_jsonl, repo_root),
            "dev_jsonl": _display_path(outputs.dev_jsonl, repo_root),
            "summary": _display_path(outputs.summary, repo_root),
            "leakage_check": _display_path(outputs.leakage_check, repo_root),
            "run_card": _display_path(outputs.run_card, repo_root),
            "human_brief": _display_path(outputs.human_brief, repo_root),
            "progress_ledger": _display_path(outputs.progress_ledger, repo_root),
        },
    }


def _negative_split_counts(
    records: Sequence[HardNegativeRecord],
    *,
    repo_root: Path,
    config: HardNegativeConfig,
) -> dict[str, dict[str, int]]:
    pages = validate_pages(load_jsonl(_resolve_path(repo_root, config.pages_manifest)))
    pages_by_id = {page.page_id: page for page in pages}
    split_counts: dict[str, dict[str, int]] = {}
    for record in records:
        negative_split = pages_by_id[record.negative_page_id].split
        split_counts.setdefault(record.split, {})
        split_counts[record.split][negative_split] = (
            split_counts[record.split].get(negative_split, 0) + 1
        )
    return {
        split: dict(sorted(counts.items()))
        for split, counts in sorted(split_counts.items())
    }


def _source_support_report(
    source_id: str,
    records: Sequence[HardNegativeRecord],
) -> dict[str, object]:
    if not records:
        return {
            "status": "zero_support",
            "support": 0,
            "reason": "no_wrong_page_candidates",
            "evidence": None,
        }
    splits: dict[str, int] = {}
    for record in records:
        splits[record.split] = splits.get(record.split, 0) + 1
    return {
        "status": "generated",
        "support": len(records),
        "source": source_id,
        "splits": dict(sorted(splits.items())),
    }


def _write_json(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_run_card(path: Path, summary: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = cast(Mapping[str, object], summary["outputs"])
    records = cast(Mapping[str, object], summary["record_counts"])
    source_support = cast(Mapping[str, object], summary["source_support"])
    text = f"""# VisDoc Hard-Negative Mining Run Card

Status: hard-negative mining checkpoint, deterministic local smoke data.

Command:

```bash
{HARD_NEGATIVE_COMMAND}
```

Inputs:
- Pages manifest: data/synthetic-smoke/pages.jsonl
- Queries/qrels manifest: data/synthetic-smoke/queries.jsonl
- Evaluated splits: train, dev
- Candidate universe: evaluated_split_pages
- final test evaluation: not_run

Outputs:
- Train triples: {outputs["train_jsonl"]}
- Dev triples: {outputs["dev_jsonl"]}
- Summary: {outputs["summary"]}
- Leakage check: {outputs["leakage_check"]}

Counts:
- Total records: {records["total"]}
- Train records: {records["train"]}
- Dev records: {records["dev"]}

Sources:
{_source_support_markdown(source_support)}

Boundaries:
- no training
- no final test evaluation
- no model download
- no GPU requirement
- no real ColPali / ColQwen execution
- no benchmark improvement claim
- no RAG or chatbot behavior
"""
    path.write_text(text, encoding="utf-8")


def _write_human_brief(path: Path, summary: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = cast(Mapping[str, object], summary["outputs"])
    records = cast(Mapping[str, object], summary["record_counts"])
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>VisDoc Hard-Negative Mining Brief</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 32px;
      line-height: 1.6;
      color: #1f2937;
    }}
    h1 {{ font-size: 24px; margin-bottom: 8px; }}
    h2 {{ font-size: 17px; margin-top: 22px; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
    .status {{
      border-left: 4px solid #2563eb;
      padding: 10px 14px;
      background: #eff6ff;
    }}
  </style>
</head>
<body>
  <h1>Phase 4 hard-negative mining checkpoint</h1>
  <div class="status"><strong>结论：</strong>已生成 train/dev hard-negative
  triples 和 leakage report；这是确定性 CPU-only 训练准备证据，不训练、
  不跑 final test、不声明 benchmark improvement。</div>
  <h2>当前状态</h2>
  <p>状态：generated。OpenSpec change：<code>add-hard-negative-mining</code>。</p>
  <h2>本阶段变化</h2>
  <p>新增 hard-negative mining CLI、配置、train/dev JSONL、summary、
  leakage check、run card 和 progress ledger entry。</p>
  <h2>关键产物</h2>
  <ul>
    <li>Train triples: <code>{outputs["train_jsonl"]}</code></li>
    <li>Dev triples: <code>{outputs["dev_jsonl"]}</code></li>
    <li>Summary: <code>{outputs["summary"]}</code></li>
    <li>Leakage: <code>{outputs["leakage_check"]}</code></li>
  </ul>
  <h2>记录数量</h2>
  <p>Total: {records["total"]}; train: {records["train"]}; dev: {records["dev"]}。</p>
  <h2>边界</h2>
  <p>不训练；不下载 ColPali/ColQwen/BGE/sentence-transformers 权重；
  不需要 GPU；不跑 final test evaluation；不把 mock visual 写成 real
  visual result；不把项目改成 RAG chatbot。</p>
  <h2>建议下一步</h2>
  <p>先 review 本 PR 的 split/leakage/source-support evidence。LoRA /
  QLoRA adaptation 需要后续单独 OpenSpec change。</p>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _update_progress_ledger(path: Path, summary: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = cast(Mapping[str, object], summary["outputs"])
    records = cast(Mapping[str, object], summary["record_counts"])
    block = f"""hard_negative_mining_status:
  status: generated
  change: add-hard-negative-mining
  command: {HARD_NEGATIVE_COMMAND}
  config: configs/hard_negatives.json
  evaluated_splits:
    - train
    - dev
  candidate_universe: evaluated_split_pages
  train_records: {records["train"]}
  dev_records: {records["dev"]}
  total_records: {records["total"]}
  evidence:
    train_jsonl: {outputs["train_jsonl"]}
    dev_jsonl: {outputs["dev_jsonl"]}
    summary: {outputs["summary"]}
    leakage_check: {outputs["leakage_check"]}
    run_card: {outputs["run_card"]}
    human_brief: {outputs["human_brief"]}
  real_visual_model_execution: not_run
  external_embeddings: not_started
  training: not_started
  final_test_evaluation: not_run
  benchmark_claim: none
"""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(
        _replace_top_level_yaml_block(existing, "hard_negative_mining_status", block),
        encoding="utf-8",
    )


def _source_support_markdown(source_support: Mapping[str, object]) -> str:
    lines: list[str] = []
    for source_id in sorted(source_support):
        report = cast(Mapping[str, object], source_support[source_id])
        lines.append(
            f"- {source_id}: status={report['status']}, support={report['support']}"
        )
    return "\n".join(lines)


def _replace_top_level_yaml_block(text: str, key: str, block: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    skipping = False
    for line in lines:
        if line.startswith(f"{key}:"):
            skipping = True
            continue
        if skipping:
            if line and not line.startswith((" ", "-")):
                skipping = False
            else:
                continue
        if not skipping:
            output.append(line)
    while output and output[-1] == "":
        output.pop()
    if output:
        output.append("")
    output.extend(block.strip("\n").splitlines())
    return "\n".join(output) + "\n"


def _source_configs(
    data: Mapping[str, object],
    *,
    default_top_k: int,
) -> dict[str, SourceConfig]:
    sources: dict[str, SourceConfig] = {}
    for source_id, value in data.items():
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source IDs must be non-empty strings")
        if not isinstance(value, Mapping):
            raise ValueError(f"source config must be an object: {source_id}")
        source_mapping = cast(Mapping[str, object], value)
        sources[source_id] = SourceConfig(
            enabled=bool(source_mapping.get("enabled", False)),
            top_k=_positive_int(source_mapping.get("top_k", default_top_k), "top_k"),
        )
    return sources


def _resolved_outputs(
    repo_root: Path,
    outputs: HardNegativeOutputs,
) -> HardNegativeOutputs:
    return HardNegativeOutputs(
        train_jsonl=_resolve_path(repo_root, outputs.train_jsonl),
        dev_jsonl=_resolve_path(repo_root, outputs.dev_jsonl),
        summary=_resolve_path(repo_root, outputs.summary),
        leakage_check=_resolve_path(repo_root, outputs.leakage_check),
        run_card=_resolve_path(repo_root, outputs.run_card),
        human_brief=_resolve_path(repo_root, outputs.human_brief),
        progress_ledger=_resolve_path(repo_root, outputs.progress_ledger),
    )


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _record_from_mapping(record: Mapping[str, object]) -> HardNegativeRecord:
    evidence = _required_mapping(record, "evidence")
    score = record.get("score")
    if score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValidationError("score must be numeric or null")
        score = float(score)
    return HardNegativeRecord(
        query_id=_required_str(record, "query_id"),
        positive_page_id=_required_str(record, "positive_page_id"),
        negative_page_id=_required_str(record, "negative_page_id"),
        split=_required_str(record, "split"),
        negative_source=_required_str(record, "negative_source"),
        rank=_positive_int(_required(record, "rank"), "rank"),
        score=score,
        candidate_universe_id=_required_str(record, "candidate_universe_id"),
        reason=_required_str(record, "reason"),
        evidence=dict(evidence),
    )


def _validate_record(record: HardNegativeRecord) -> None:
    if record.rank < 1:
        raise ValidationError("rank must be positive")
    for field_name, value in (
        ("query_id", record.query_id),
        ("positive_page_id", record.positive_page_id),
        ("negative_page_id", record.negative_page_id),
        ("split", record.split),
        ("negative_source", record.negative_source),
        ("candidate_universe_id", record.candidate_universe_id),
        ("reason", record.reason),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_name} must be a non-empty string")


def _dedupe_preference(record: HardNegativeRecord) -> tuple[int, float, str]:
    score = record.score if record.score is not None else float("-inf")
    return (record.rank, -score, record.reason)


def _record_sort_key(record: HardNegativeRecord) -> tuple[int, str, str, str, int, str]:
    split_order = {"train": 0, "dev": 1, "test": 2}.get(record.split, 99)
    return (
        split_order,
        record.query_id,
        record.positive_page_id,
        record.negative_source,
        record.rank,
        record.negative_page_id,
    )


def _required(record: Mapping[str, object], field: str) -> object:
    if field not in record:
        raise ValueError(f"missing required field: {field}")
    return record[field]


def _required_mapping(record: Mapping[str, object], field: str) -> Mapping[str, object]:
    value = _required(record, field)
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return cast(Mapping[str, object], value)


def _required_str(record: Mapping[str, object], field: str) -> str:
    value = _required(record, field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _required_str_tuple(record: Mapping[str, object], field: str) -> tuple[str, ...]:
    value = _required(record, field)
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field} must be a list of non-empty strings")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain non-empty strings")
        values.append(item)
    if not values:
        raise ValueError(f"{field} must not be empty")
    return tuple(values)


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value
