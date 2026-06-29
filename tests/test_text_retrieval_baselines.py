"""Tests for Phase 2 text retrieval baselines."""

from __future__ import annotations

from pathlib import Path

import pytest

from visdoc_retrieve import text_retrieval
from visdoc_retrieve.data_schema import ValidationError, write_jsonl
from visdoc_retrieve.text_retrieval import BM25Retriever, TextPage, load_text_corpus


def test_text_corpus_loader_loads_manifest_text_and_split_metadata() -> None:
    corpus = load_text_corpus(
        repo_root=Path.cwd(),
        pages_manifest=Path("data/synthetic-smoke/pages.jsonl"),
        queries_manifest=Path("data/synthetic-smoke/queries.jsonl"),
    )

    page = corpus.pages_by_id["manual-b-p01"]
    query = corpus.queries_by_id["manual-b-p01-q01"]

    assert page.split == "dev"
    assert page.family_id == "manual-b"
    assert "Optical Switch Service Manual" in page.text
    assert query.split == "dev"
    assert query.positive_page_ids == ("manual-b-p01",)


def test_text_corpus_loader_fails_fast_on_missing_text_artifact(
    tmp_path: Path,
) -> None:
    pages_path = tmp_path / "pages.jsonl"
    queries_path = tmp_path / "queries.jsonl"
    write_jsonl(
        pages_path,
        [
            {
                "page_id": "manual-a-p01",
                "doc_id": "manual-a",
                "page_number": 1,
                "image_path": "data/synthetic-smoke/pages/manual-a/p01.png",
                "text_path": "data/synthetic-smoke/text/manual-a/missing.txt",
                "family_id": "manual-a",
                "split": "train",
                "content_hash": "a" * 64,
            }
        ],
    )
    write_jsonl(
        queries_path,
        [
            {
                "query_id": "manual-a-p01-q01",
                "query": "Which table limit appears?",
                "positive_page_ids": ["manual-a-p01"],
                "family_id": "manual-a",
                "split": "train",
                "query_type": "table",
                "source": {
                    "doc_id": "manual-a",
                    "page_id": "manual-a-p01",
                    "page_number": 1,
                    "description": "toy query",
                },
            }
        ],
    )

    with pytest.raises(ValidationError, match="missing text artifact"):
        load_text_corpus(
            repo_root=Path.cwd(),
            pages_manifest=pages_path,
            queries_manifest=queries_path,
        )


def test_bm25_ranks_lexical_match_first_and_breaks_ties_by_page_id() -> None:
    pages = (
        TextPage("page-b", "dev", "family", "alpha pump valve"),
        TextPage("page-a", "dev", "family", "alpha pump valve"),
        TextPage("page-c", "dev", "family", "unrelated optical switch"),
    )

    ranking = BM25Retriever(pages).rank("alpha pump")

    assert [item.page_id for item in ranking] == ["page-a", "page-b", "page-c"]


def test_lexical_cosine_public_contract_replaces_dense_text_name() -> None:
    assert hasattr(text_retrieval, "LexicalCosineRetriever")
    assert not hasattr(text_retrieval, "DenseTextRetriever")

    pages = (
        TextPage("page-b", "dev", "family", "controller reset sequence"),
        TextPage("page-a", "dev", "family", "controller reset sequence"),
        TextPage("page-c", "dev", "family", "optical switch diagram"),
    )
    retriever = text_retrieval.LexicalCosineRetriever(pages)

    first = retriever.rank("controller reset")
    second = retriever.rank("controller reset")

    assert retriever.method_id == "lexical_cosine"
    assert [item.page_id for item in first] == ["page-a", "page-b", "page-c"]
    assert [(item.page_id, item.score) for item in first] == [
        (item.page_id, item.score) for item in second
    ]
    assert retriever.uses_external_embeddings is False


def test_neural_text_retriever_uses_deterministic_local_stub_provider() -> None:
    pages = (
        TextPage("page-b", "dev", "family", "controller reset sequence"),
        TextPage("page-a", "dev", "family", "controller reset sequence"),
        TextPage("page-c", "dev", "family", "optical switch diagram"),
    )
    provider = text_retrieval.LocalStubEmbeddingProvider()
    retriever = text_retrieval.NeuralTextRetriever(pages, provider=provider)

    first = retriever.rank("controller reset")
    second = retriever.rank("controller reset")

    assert retriever.method_id == "neural_text"
    assert retriever.uses_external_embeddings is False
    assert retriever.provider_status == {
        "provider": "local_stub",
        "status": "mock_or_local_stub",
        "external_embeddings_enabled": False,
        "network_required": False,
        "gpu_required": False,
        "model_download_required": False,
        "embedding_cache_required": False,
    }
    assert [item.page_id for item in first] == [item.page_id for item in second]
    assert [(item.page_id, item.score) for item in first] == [
        (item.page_id, item.score) for item in second
    ]


def test_bm25_lexical_rrf_combines_rankings_and_breaks_ties_by_page_id() -> None:
    pages = (
        TextPage("page-a", "dev", "family", "alpha token"),
        TextPage("page-b", "dev", "family", "beta token"),
        TextPage("page-c", "dev", "family", "gamma token"),
    )

    ranking = text_retrieval.BM25LexicalRrfRetriever(
        pages,
        bm25_rankings={"query": ("page-a", "page-b", "page-c")},
        lexical_rankings={"query": ("page-b", "page-a", "page-c")},
    ).rank("query")

    assert [item.page_id for item in ranking] == ["page-a", "page-b", "page-c"]


def test_bm25_neural_rrf_combines_rankings_and_breaks_ties_by_page_id() -> None:
    pages = (
        TextPage("page-a", "dev", "family", "alpha token"),
        TextPage("page-b", "dev", "family", "beta token"),
        TextPage("page-c", "dev", "family", "gamma token"),
    )

    ranking = text_retrieval.BM25NeuralRrfRetriever(
        pages,
        bm25_rankings={"query": ("page-a", "page-b", "page-c")},
        neural_rankings={"query": ("page-b", "page-a", "page-c")},
    ).rank("query")

    assert [item.page_id for item in ranking] == ["page-a", "page-b", "page-c"]
