## Context

VisDoc-Retrieve is through Phase 3A plus a Phase 2.5 text/candidate-universe
clarification. The repository already has manifest validation, a fixed
synthetic smoke corpus, deterministic text baselines, retrieval metrics, and a
deterministic local visual-smoke report. What is missing is a single bounded MVP
entry point that runs the page-retrieval path end to end and emits one evidence
bundle without implying final benchmark performance.

## Goals / Non-Goals

**Goals:**

- Provide one clean-checkout command for the diagnostic MVP:
  `PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json`.
- Use only committed synthetic smoke manifests and artifacts.
- Keep evaluated queries and candidate page universe explicitly separated.
- Run configured text baselines and a deterministic visual late-interaction
  mock scaffold in the same report surface.
- Write deterministic rankings, metrics, run card, mock embedding cache, human
  brief, and ledger evidence.
- Keep all metrics labeled diagnostic/smoke.

**Non-Goals:**

- Real ColPali/ColQwen execution, external embeddings, GPU work, model
  downloads, hard-negative mining, LoRA/QLoRA training, final-test evaluation,
  chatbot/RAG app behavior, deployment, and benchmark-improvement claims.
- Replacing the Phase 2.5 text report or Phase 3A visual-smoke report.
- Archiving the OpenSpec change, committing, pushing, or merging.

## Decisions

1. Add a small MVP layer instead of changing existing report runners.
   - Rationale: existing text and visual reports are archived phase evidence.
     The MVP should compose their primitives and produce a new evidence bundle
     without rewriting prior artifact meaning.
   - Alternative considered: extend both report runners directly. This would
     blur the archived phase boundaries and duplicate report-specific logic.

2. Put visual late-interaction scaffold primitives behind a new protocol and
   deterministic mock retriever.
   - Rationale: the MVP needs an interface-shaped surface that resembles future
     visual retrievers while remaining CPU-only and truthful.
   - Alternative considered: rename `VisualSmokeRetriever`. That risks
     presenting the Phase 3A smoke runner as a broader retriever contract.

3. Use MaxSim over validated numeric token embeddings with fail-fast shape
   checks and zero scores for empty query/page token sets.
   - Rationale: MaxSim is the core late-interaction scoring shape to exercise,
     while empty handling and shape checks prevent silent invalid metrics.

4. Persist a JSON mock embedding cache as evidence, not as a production cache.
   - Rationale: the DoD requires cache schema and round-trip coverage. A
     deterministic JSON cache is inspectable, small, and does not introduce
     external embedding artifacts.

5. Compute subset metrics by query type with explicit support.
   - Rationale: the synthetic data already carries `query_type` tags for text,
     table, figure, layout, and OCR-failure style subsets. If a future config
     has zero support, the report must record `support: 0` and `metrics: null`
     instead of fabricating perfect scores.

## Risks / Trade-offs

- Mock visual scores may look like retrieval numbers -> Mitigation: every MVP
  artifact records `diagnostic_only`, `mock_visual`, no real model inference,
  and no benchmark claim.
- The MVP may duplicate small pieces of report formatting -> Mitigation:
  reuse loaders, retrievers, and metric utilities; keep new formatting local to
  the MVP artifact bundle.
- Candidate-universe widening could be mistaken for test evaluation ->
  Mitigation: keep default `evaluated_split_pages` over `dev`, record final
  test as `not_run`, and test split boundaries.
- Cache artifacts could be misread as external embeddings -> Mitigation:
  include cache metadata that states `provider: deterministic_mock` and all
  external/network/GPU/model-download flags are false.
