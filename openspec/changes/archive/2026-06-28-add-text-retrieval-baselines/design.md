## Context

Phase 1 materialized a deterministic synthetic smoke corpus with page manifests,
query relevance manifests, rendered page images, and OCR-like text artifacts.
Phase 2 needs text-only retrieval baselines so future visual late-interaction
work has a meaningful comparison point. The implementation must remain local,
CPU-friendly, deterministic in tests, and bounded to diagnostic smoke reports.

This change consumes existing manifest contracts instead of changing them. It
also preserves the project boundary that final test evaluation and improvement
claims are not allowed until a later frozen-test phase explicitly opens that
surface.

## Goals / Non-Goals

**Goals:**

- Load Phase 1 page/query manifests and text artifacts into a text retrieval
  corpus without reading page images.
- Implement deterministic BM25, dense-text, and hybrid/RRF retrieval baselines.
- Compute Recall@1, Recall@5, MRR, NDCG@10, latency/query diagnostics, index
  size diagnostics, and hard-negative hit-rate status.
- Generate a config-driven diagnostic text-baseline report on the synthetic
  smoke corpus using local validation only.
- Add toy ranking and metric tests that prove deterministic behavior,
  tie-breaking, and report structure.

**Non-Goals:**

- No ColPali, ColQwen, visual late-interaction, image embedding, reranker, or
  multimodal inference path.
- No hard-negative mining output or training triple generation.
- No LoRA/QLoRA training, GPU job, A100 dependency, model checkpoint, or adapter
  artifact.
- No required network download, external embedding model, or FAISS dependency
  for local validation.
- No final test split evaluation and no benchmark improvement claim.

## Decisions

1. Use a manifest-backed corpus loader.

   The loader will validate `pages.jsonl` and `queries.jsonl`, resolve
   repo-relative `text_path` values, and return page/query objects suitable for
   retrieval. It will fail on missing text artifacts or duplicate IDs. The
   alternative, scanning text directories directly, would bypass the Phase 1
   data contract and make split handling fragile.

2. Implement a small internal BM25 baseline.

   BM25 is core to the comparison, but adding a dependency such as
   `rank-bm25` is unnecessary for the smoke corpus and toy tests. A compact
   internal implementation keeps tokenization, scoring, and tie-breaking under
   project control. The alternative, depending on a package, would be acceptable
   later but adds little value for this deterministic baseline phase.

3. Make the default dense baseline deterministic and local.

   The default dense-text baseline will use a stable local lexical vectorizer
   suitable for tests and smoke reporting. Optional sentence-transformer or
   FAISS-backed paths may be designed behind config, but they must not be
   required by default validation. The alternative, requiring BGE or
   sentence-transformers immediately, would make Phase 2 dependent on model
   downloads and hardware/network state.

4. Use RRF for sparse-dense hybrid fusion.

   Reciprocal rank fusion combines BM25 and dense rankings from rank positions
   rather than score calibration. This keeps the hybrid baseline deterministic
   and easy to test across methods with different score scales. The alternative,
   weighted score interpolation, would require method-specific normalization
   before the project has real benchmark evidence.

5. Exclude the final test split by default.

   The baseline report will run on configured non-final splits, with the default
   config using the development split and recording final-test status as
   `not_run`. This preserves the project rule against tuning or claiming results
   from the final test split. The alternative, evaluating all splits for
   convenience, would create avoidable leakage and public-claim pressure.

6. Treat hard-negative hit rate as conditional.

   The report schema will include hard-negative hit-rate status, but the metric
   is `not_available` unless a later phase supplies hard-negative triples. This
   avoids confusing Phase 2 baselines with hard-negative mining.

## Risks / Trade-offs

- Local dense baseline is not a production embedding model -> Label it as the
  deterministic default and keep external embedding support optional.
- Internal BM25 may differ from package implementations -> Cover tokenization,
  scoring order, and stable tie-breaking with toy tests.
- Latency values are machine-dependent -> Treat latency/query as diagnostic
  metadata, not a benchmark claim or strict expected value.
- Synthetic smoke metrics can be overinterpreted -> Report wording and progress
  ledger must state diagnostic-only status and keep final test `not_run`.
- Optional external model paths can expand scope -> Keep them disabled by
  default and outside acceptance unless a later OpenSpec change requires them.
