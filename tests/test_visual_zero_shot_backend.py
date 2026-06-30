"""Tests for the optional visual zero-shot backend checkpoint."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
import yaml

from visdoc_retrieve.data_schema import ValidationError, load_jsonl, write_jsonl
from visdoc_retrieve.mvp_pipeline import load_mvp_config, run_mvp_pipeline
from visdoc_retrieve.visual_retrieval import (
    MockVisualRetriever,
    VisualPage,
    VisualQuery,
    maxsim_score,
)


def test_visual_zero_shot_example_config_parses_and_is_not_default() -> None:
    from visdoc_retrieve.visual_zero_shot import load_visual_zero_shot_config

    config = load_visual_zero_shot_config(
        Path("configs/visual_zero_shot.local.example.json")
    )

    assert config.name == "visual-zero-shot-local-smoke"
    assert config.backend.name == "local_visual_model"
    assert config.backend.model_path == Path("local-models/colpali-or-colqwen")
    assert config.backend.model_id == "local-colpali-or-colqwen"
    assert config.backend.device == "cpu"
    assert config.backend.batch_size == 1
    assert config.backend.cache_path == Path(
        ".local/visual-zero-shot/cache/embeddings.json"
    )
    assert config.corpus_path == Path("data/synthetic-smoke/pages.jsonl")
    assert config.query_path == Path("data/synthetic-smoke/queries.jsonl")
    assert config.pages_manifest == Path("data/synthetic-smoke/pages.jsonl")
    assert config.queries_manifest == Path("data/synthetic-smoke/queries.jsonl")
    assert config.qrels_path == Path("data/synthetic-smoke/queries.jsonl")
    assert config.outputs.run_card == Path("reports/visual-zero-shot/run-card.md")
    assert config.ci_required is False

    mvp_config = load_mvp_config(Path("configs/mvp.json"))
    assert mvp_config.visual_methods == ("mock_visual",)


def test_missing_local_model_path_fails_clearly(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot import (
        VisualZeroShotConfigError,
        check_visual_zero_shot_config,
        load_visual_zero_shot_config,
    )

    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=tmp_path / "missing-model",
    )
    config = load_visual_zero_shot_config(config_path)

    with pytest.raises(VisualZeroShotConfigError, match="local model path"):
        check_visual_zero_shot_config(config, repo_root=Path.cwd())


def test_qrels_path_must_be_query_relevance_manifest(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot import (
        VisualZeroShotConfigError,
        check_visual_zero_shot_config,
        load_visual_zero_shot_config,
    )

    model_path = tmp_path / "model"
    model_path.mkdir()
    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=model_path,
        qrels_path="data/synthetic-smoke/pages.jsonl",
    )
    config = load_visual_zero_shot_config(config_path)

    with pytest.raises(VisualZeroShotConfigError, match="qrels"):
        check_visual_zero_shot_config(config, repo_root=Path.cwd())


def test_qrels_path_must_match_query_relevance_records(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot import (
        VisualZeroShotConfigError,
        check_visual_zero_shot_config,
        load_visual_zero_shot_config,
    )

    model_path = tmp_path / "model"
    model_path.mkdir()
    qrels_path = tmp_path / "qrels.jsonl"
    records = load_jsonl(Path("data/synthetic-smoke/queries.jsonl"))
    records[0]["positive_page_ids"] = ["manual-a-p02"]
    records[0]["source"] = {
        "doc_id": "manual-a",
        "page_id": "manual-a-p02",
        "page_number": 2,
        "description": "synthetic mismatch",
    }
    write_jsonl(qrels_path, records)
    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=model_path,
        qrels_path=str(qrels_path),
    )
    config = load_visual_zero_shot_config(config_path)

    with pytest.raises(VisualZeroShotConfigError, match="positive pages"):
        check_visual_zero_shot_config(config, repo_root=Path.cwd())


def test_config_rejects_non_boolean_policy_values(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot import (
        VisualZeroShotConfigError,
        load_visual_zero_shot_config,
    )

    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=tmp_path / "model",
        ci_required="false",
    )

    with pytest.raises(VisualZeroShotConfigError, match="ci_required"):
        load_visual_zero_shot_config(config_path)

    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=tmp_path / "model",
        local_files_only="true",
    )

    with pytest.raises(VisualZeroShotConfigError, match="local_files_only"):
        load_visual_zero_shot_config(config_path)


def test_run_visual_zero_shot_check_config_reports_missing_model(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from visdoc_retrieve.run_visual_zero_shot import main

    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=tmp_path / "missing-model",
    )

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--repo-root",
            str(Path.cwd()),
            "--check-config",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "local model path does not exist" in captured.err
    assert "mock_visual" not in captured.out


def test_run_visual_zero_shot_real_run_reports_missing_model(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from visdoc_retrieve.run_visual_zero_shot import main

    config_path = _write_zero_shot_config(
        tmp_path,
        model_path=tmp_path / "missing-model",
    )

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--repo-root",
            str(Path.cwd()),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "local model path does not exist" in captured.err
    assert "mock_visual" not in captured.out


def test_real_backend_module_import_is_side_effect_light() -> None:
    before = set(sys.modules)

    module = importlib.import_module("visdoc_retrieve.visual_zero_shot_backend")

    after = set(sys.modules)
    assert hasattr(module, "LocalVisualModelBackend")
    assert "torch" not in after - before
    assert "transformers" not in after - before
    assert "colpali_engine" not in after - before


def test_visual_embedding_cache_round_trips_and_scores(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot_backend import (
        VisualEmbeddingCache,
        load_visual_embedding_cache,
        write_visual_embedding_cache,
    )

    cache = VisualEmbeddingCache(
        metadata={
            "schema_version": "visual_token_embedding_cache/v1",
            "backend_name": "local_visual_model",
            "provider": "real_local_model",
            "model_reference": "local-models/colpali-or-colqwen",
            "embedding_dimensions": 2,
            "query_count": 1,
            "page_count": 1,
            "network_required": False,
            "model_download_required": False,
        },
        query_embeddings={"q1": ((1.0, 0.0), (0.0, 1.0))},
        page_embeddings={"p1": ((1.0, 0.0), (0.25, 0.75))},
    )
    cache_path = tmp_path / "real-cache.json"

    write_visual_embedding_cache(cache_path, cache)
    loaded = load_visual_embedding_cache(cache_path)

    assert loaded == cache
    assert maxsim_score(
        query_token_embeddings=loaded.query_embeddings["q1"],
        page_token_embeddings=loaded.page_embeddings["p1"],
    ) == pytest.approx(0.875)


def test_visual_embedding_cache_rejects_shape_mismatch(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot_backend import load_visual_embedding_cache

    cache_path = tmp_path / "bad-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "schema_version": "visual_token_embedding_cache/v1",
                    "backend_name": "local_visual_model",
                    "provider": "real_local_model",
                    "model_reference": "local-models/colpali-or-colqwen",
                    "embedding_dimensions": 2,
                    "query_count": 1,
                    "page_count": 1,
                },
                "query_embeddings": {"q1": [[1.0, 0.0], [1.0]]},
                "page_embeddings": {"p1": [[1.0, 0.0]]},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="same dimensions"):
        load_visual_embedding_cache(cache_path)


def test_visual_embedding_cache_requires_provenance_and_counts(
    tmp_path: Path,
) -> None:
    from visdoc_retrieve.visual_zero_shot_backend import load_visual_embedding_cache

    cache_path = tmp_path / "bad-cache.json"
    required_metadata_cases = [
        ("schema_version", "schema_version"),
        ("backend_name", "backend_name"),
        ("provider", "provider"),
        ("model_reference", "model_reference"),
        ("embedding_dimensions", "embedding_dimensions"),
        ("query_count", "query_count"),
        ("page_count", "page_count"),
    ]
    for missing_key, error_match in required_metadata_cases:
        metadata = _valid_cache_metadata()
        del metadata[missing_key]
        _write_cache_payload(cache_path, metadata=metadata)
        with pytest.raises(ValidationError, match=error_match):
            load_visual_embedding_cache(cache_path)

    metadata = _valid_cache_metadata()
    metadata["query_count"] = 2
    _write_cache_payload(cache_path, metadata=metadata)

    with pytest.raises(ValidationError, match="query_count"):
        load_visual_embedding_cache(cache_path)

    metadata = _valid_cache_metadata()
    metadata["page_count"] = 2
    _write_cache_payload(cache_path, metadata=metadata)

    with pytest.raises(ValidationError, match="page_count"):
        load_visual_embedding_cache(cache_path)


def test_visual_embedding_cache_rejects_non_numeric_values(tmp_path: Path) -> None:
    from visdoc_retrieve.visual_zero_shot_backend import load_visual_embedding_cache

    cache_path = tmp_path / "bad-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "schema_version": "visual_token_embedding_cache/v1",
                    "backend_name": "local_visual_model",
                    "provider": "real_local_model",
                    "model_reference": "local-models/colpali-or-colqwen",
                    "embedding_dimensions": 2,
                    "query_count": 1,
                    "page_count": 1,
                },
                "query_embeddings": {"q1": [[1.0, "not-a-number"]]},
                "page_embeddings": {"p1": [[1.0, 0.0]]},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="numeric"):
        load_visual_embedding_cache(cache_path)


def test_mock_visual_backend_stays_deterministic() -> None:
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

    assert [item.page_id for item in retriever.rank(query)] == [
        "page-a",
        "page-b",
        "page-c",
    ]
    assert retriever.rank(query) == retriever.rank(query)
    assert retriever.uses_external_model is False
    assert retriever.gpu_required is False


def test_mvp_pipeline_remains_mock_only_by_default() -> None:
    config = load_mvp_config(Path("configs/mvp.json"))

    run_mvp_pipeline(config, repo_root=Path.cwd())

    metrics = json.loads(Path("reports/mvp/metrics.json").read_text(encoding="utf-8"))
    assert metrics["boundary"]["real_colpali_or_colqwen_execution"] is False
    assert metrics["boundary"]["model_download_required"] is False
    assert metrics["boundary"]["benchmark_claim"] == "none"
    assert metrics["methods"]["mock_visual"]["method_kind"] == "visual_mock"
    assert metrics["methods"]["mock_visual"]["boundary"][
        "real_colpali_or_colqwen_execution"
    ] is False
    ledger = yaml.safe_load(
        Path("reports/progress-ledger.yaml").read_text(encoding="utf-8")
    )
    assert ledger["mvp_retrieval_pipeline_status"]["visual_retriever_status"] == (
        "deterministic_mock_scaffold"
    )
    assert ledger["mvp_retrieval_pipeline_status"]["real_visual_model_execution"] == (
        "not_started"
    )


def _write_zero_shot_config(
    tmp_path: Path,
    *,
    model_path: Path,
    qrels_path: str = "data/synthetic-smoke/queries.jsonl",
    ci_required: object = False,
    local_files_only: object = True,
) -> Path:
    config_path = tmp_path / "visual_zero_shot.json"
    config_path.write_text(
        json.dumps(
            {
                "name": "visual-zero-shot-local-smoke",
                "ci_required": ci_required,
                "corpus_path": "data/synthetic-smoke/pages.jsonl",
                "query_path": "data/synthetic-smoke/queries.jsonl",
                "qrels_path": qrels_path,
                "evaluated_splits": ["dev"],
                "candidate_universe": "evaluated_split_pages",
                "final_test_split": "test",
                "backend": {
                    "name": "local_visual_model",
                    "model_path": str(model_path),
                    "model_id": "local-colpali-or-colqwen",
                    "device": "cpu",
                    "batch_size": 1,
                    "cache_path": str(
                        tmp_path / "cache" / "visual-embeddings.json"
                    ),
                    "local_files_only": local_files_only,
                },
                "outputs": {
                    "metrics": "reports/visual-zero-shot/metrics.json",
                    "rankings": "reports/visual-zero-shot/rankings.csv",
                    "run_card": "reports/visual-zero-shot/run-card.md",
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _valid_cache_metadata() -> dict[str, object]:
    return {
        "schema_version": "visual_token_embedding_cache/v1",
        "backend_name": "local_visual_model",
        "provider": "real_local_model",
        "model_reference": "local-models/colpali-or-colqwen",
        "embedding_dimensions": 2,
        "query_count": 1,
        "page_count": 1,
    }


def _write_cache_payload(
    path: Path,
    *,
    metadata: dict[str, object],
) -> None:
    path.write_text(
        json.dumps(
            {
                "metadata": metadata,
                "query_embeddings": {"q1": [[1.0, 0.0]]},
                "page_embeddings": {"p1": [[1.0, 0.0]]},
            }
        ),
        encoding="utf-8",
    )
