## Why

VisDoc-Retrieve now has deterministic page/query manifests and OCR-like text
artifacts, but it still lacks the text retrieval baselines needed before any
visual late-interaction comparison is meaningful. This change establishes Phase
2 sparse, dense, and hybrid text baselines on the smoke corpus without entering
ColPali inference, training, hard-negative mining, or final benchmark claims.

## What Changes

- Add a config-driven text retrieval baseline report over Phase 1 page/query
  manifests and text artifacts.
- Add deterministic BM25 retrieval over extracted/OCR-like page text.
- Add a deterministic local dense-text baseline suitable for tests and smoke
  reports, with any external embedding model path kept optional and disabled by
  default.
- Add sparse-dense hybrid retrieval using reciprocal rank fusion (RRF).
- Add retrieval metric computation for Recall@1, Recall@5, MRR, NDCG@10,
  latency/query diagnostics, index-size diagnostics, and hard-negative hit-rate
  status when hard-negative triples exist.
- Add toy ranking and metric tests so baseline behavior is deterministic and
  independent of network, GPU hardware, model downloads, or A100 access.
- Update progress documentation and a Phase 2 Human Brief after implementation
  while keeping public claims diagnostic-only.
- Keep ColPali/ColQwen inference, image retrieval, reranking, hard-negative
  mining outputs, LoRA/QLoRA training, FAISS-only requirements, final test
  evaluation, and improvement claims out of this change.

## Capabilities

### New Capabilities

- `text-retrieval-baselines`: Defines corpus loading and deterministic BM25,
  dense-text, and hybrid/RRF retrievers over Phase 1 text artifacts.
- `retrieval-evaluation-metrics`: Defines deterministic retrieval metrics and
  config-driven text-baseline report semantics, including diagnostic latency and
  index-size fields.

### Modified Capabilities

- None.

## Impact

- Affected code: new retrieval/evaluation/reporting modules under
  `src/visdoc_retrieve/`, focused tests under `tests/`, a text-baseline config
  under `configs/`, and diagnostic report artifacts under `reports/`.
- Affected data: consumes existing `data/synthetic-smoke/` manifests and text
  artifacts; does not modify Phase 1 data schemas or generated corpus contents.
- Affected dependencies: prefer standard-library and existing project
  dependencies for deterministic smoke tests; optional embedding or FAISS paths
  must not be required for local validation.
- No visual retriever, model checkpoint, embedding download, GPU job, training
  artifact, hard-negative triple output, final test run, or benchmark
  improvement claim is introduced.
