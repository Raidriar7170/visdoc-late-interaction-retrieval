"""Tests for the diagnostic MVP retrieval pipeline."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

from visdoc_retrieve.data_schema import ValidationError
from visdoc_retrieve.mvp_pipeline import load_mvp_config, run_mvp_pipeline
from visdoc_retrieve.visual_retrieval import (
    MockVisualRetriever,
    VisualPage,
    VisualQuery,
    build_mock_embedding_cache,
    load_mock_embedding_cache,
    maxsim_score,
    write_mock_embedding_cache,
)


def test_maxsim_scores_valid_embeddings_and_handles_empty_tokens() -> None:
    assert maxsim_score(
        query_token_embeddings=((1.0, 0.0), (0.0, 1.0)),
        page_token_embeddings=((1.0, 0.0), (0.5, 0.5)),
    ) == pytest.approx(0.75)

    assert (
        maxsim_score(query_token_embeddings=(), page_token_embeddings=((1.0,),))
        == 0.0
    )
    assert (
        maxsim_score(query_token_embeddings=((1.0,),), page_token_embeddings=())
        == 0.0
    )


def test_maxsim_rejects_inconsistent_embedding_shapes() -> None:
    with pytest.raises(ValidationError, match="same dimensions"):
        maxsim_score(
            query_token_embeddings=((1.0, 0.0), (1.0,)),
            page_token_embeddings=((1.0, 0.0),),
        )

    with pytest.raises(ValidationError, match="same dimensions"):
        maxsim_score(
            query_token_embeddings=((1.0, 0.0),),
            page_token_embeddings=((1.0, 0.0, 0.0),),
        )


def test_mock_visual_retriever_is_deterministic_and_cache_round_trips(
    tmp_path: Path,
) -> None:
    pages = (
        VisualPage("page-b", "dev", "family", b"alpha pump panel"),
        VisualPage("page-a", "dev", "family", b"alpha pump panel"),
        VisualPage("page-c", "dev", "family", b"unrelated optical switch"),
    )
    query = VisualQuery(
        query_id="q-alpha",
        query="alpha pump",
        positive_page_ids=("page-a",),
        split="dev",
        family_id="family",
        query_type="text",
    )
    retriever = MockVisualRetriever(pages)

    first = retriever.rank(query)
    second = retriever.rank(query)

    assert [item.page_id for item in first] == ["page-a", "page-b", "page-c"]
    assert [(item.page_id, item.score) for item in first] == [
        (item.page_id, item.score) for item in second
    ]
    assert retriever.uses_external_model is False
    assert retriever.gpu_required is False

    cache = build_mock_embedding_cache(retriever, (query,))
    cache_path = tmp_path / "mock-visual-cache.json"
    write_mock_embedding_cache(cache_path, cache)
    loaded = load_mock_embedding_cache(cache_path)

    assert loaded == cache
    assert loaded.metadata["provider"] == "deterministic_mock"
    assert loaded.metadata["network_required"] is False
    assert loaded.metadata["gpu_required"] is False
    assert loaded.metadata["model_download_required"] is False
    assert loaded.metadata["external_embeddings_enabled"] is False
    assert loaded.metadata["embedding_dimensions"] == 16
    assert loaded.query_embeddings["q-alpha"] == retriever.embed_query(query)
    assert set(loaded.page_embeddings) == {"page-a", "page-b", "page-c"}


def test_mvp_pipeline_writes_default_smoke_artifacts_and_boundaries() -> None:
    config = load_mvp_config(Path("configs/mvp.json"))

    report = run_mvp_pipeline(config, repo_root=Path.cwd())

    metrics_path = Path("reports/mvp/metrics.json")
    rankings_path = Path("reports/mvp/rankings.csv")
    run_card_path = Path("reports/mvp/run-card.md")
    cache_path = Path("reports/mvp/mock-visual-embeddings.json")
    human_brief_path = Path(
        "docs/human-briefs/2026-06-30-visdoc-mvp.html"
    )

    assert metrics_path.is_file()
    assert rankings_path.is_file()
    assert run_card_path.is_file()
    assert cache_path.is_file()
    assert human_brief_path.is_file()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert report["metrics"] == metrics
    assert metrics["status"] == "diagnostic_smoke_only"
    assert metrics["final_test_status"] == "not_run"
    assert metrics["candidate_universe"] == {
        "name": "evaluated_split_pages",
        "candidate_page_count": 8,
        "candidate_split_counts": {"dev": 8},
        "evaluated_query_count": 24,
        "evaluated_splits": ["dev"],
    }
    assert sorted(metrics["methods"]) == [
        "bm25",
        "bm25_lexical_rrf",
        "lexical_cosine",
        "mock_visual",
    ]
    assert "neural_text" not in metrics["methods"]

    for method in metrics["methods"].values():
        overall = method["overall"]
        assert overall["support"] == 24
        assert overall["metrics"]["evaluated_queries"] == 24
        assert overall["metrics"]["ranked_pages_per_query"] == 8
        for metric_name in ("recall_at_1", "recall_at_5", "mrr", "ndcg_at_10"):
            assert metric_name in overall["metrics"]
        for query_type in ("text", "table", "figure", "layout", "ocr_failure"):
            subset = method["by_query_type"][query_type]
            if subset["support"] == 0:
                assert subset["metrics"] is None
            else:
                assert subset["metrics"]["evaluated_queries"] == subset["support"]

    with rankings_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["method"] for row in rows} == set(metrics["methods"])
    assert len({row["query_id"] for row in rows}) == 24
    assert {row["candidate_universe"] for row in rows} == {"evaluated_split_pages"}
    assert max(int(row["rank"]) for row in rows) == 8

    run_card = run_card_path.read_text(encoding="utf-8")
    brief = human_brief_path.read_text(encoding="utf-8")
    assert "deterministic mock scaffold" in run_card
    assert "not real ColPali or ColQwen execution" in run_card
    assert "diagnostic smoke" in brief
    assert "not real ColPali or ColQwen execution" in brief

    ledger = yaml.safe_load(
        Path("reports/progress-ledger.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(ledger, dict)
    mvp_status = ledger["mvp_retrieval_pipeline_status"]
    assert mvp_status["status"] == "diagnostic_smoke_generated"
    assert mvp_status["command"] == (
        "PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json"
    )
    assert mvp_status["candidate_universe"] == "evaluated_split_pages"
    assert mvp_status["candidate_page_count"] == 8
    assert mvp_status["candidate_split_counts"] == {"dev": 8}
    assert mvp_status["evaluated_query_count"] == 24
    assert mvp_status["ranked_pages_per_query"] == 8
    assert mvp_status["enabled_methods"] == [
        "bm25",
        "lexical_cosine",
        "bm25_lexical_rrf",
        "mock_visual",
    ]
    assert mvp_status["visual_cache"] == {
        "schema": "mock_visual_embedding_cache/v1",
        "path": "reports/mvp/mock-visual-embeddings.json",
        "provider": "deterministic_mock",
        "external_embeddings_enabled": False,
        "network_required": False,
        "gpu_required": False,
        "model_download_required": False,
    }
    assert mvp_status["evidence"] == {
        "metrics": "reports/mvp/metrics.json",
        "rankings": "reports/mvp/rankings.csv",
        "run_card": "reports/mvp/run-card.md",
        "human_brief": (
            "docs/human-briefs/2026-06-30-visdoc-mvp.html"
        ),
    }
    assert mvp_status["real_visual_model_execution"] == "not_started"
    assert mvp_status["external_embeddings"] == "not_started"
    assert mvp_status["hard_negative_mining"] == "not_started"
    assert mvp_status["training"] == "not_started"
    assert mvp_status["final_test_evaluation"] == "not_run"
