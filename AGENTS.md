# Repository Agent Instructions

OpenSpec is the durable source of truth for scoped changes in this repository.
When `openspec/config.yaml` is present, use the relevant OpenSpec proposal,
design, specs, and tasks before implementing non-trivial changes.

## Current Phase Boundary

The repository is currently through Phase 3A, with Phase 2.5
text/candidate-universe clarification applied:

- Phase 1 synthetic corpus and manifest validation exist under
  `data/synthetic-smoke/` and `src/visdoc_retrieve/data_schema.py`.
- Phase 2 text-only diagnostic baselines exist for the synthetic smoke `dev`
  split, including deterministic BM25, local lexical cosine, retrieval
  metrics, and diagnostic report generation.
- Phase 2.5 clarifies text candidate universes and method naming. The default
  text diagnostic config uses `evaluated_split_pages`, ranks 24 dev queries
  over 8 dev pages, records candidate split counts and ranked-page support,
  and includes a deterministic local-stub `neural_text` method plus
  `bm25_lexical_rrf` and `bm25_neural_rrf` method IDs. External embeddings,
  network access, GPU execution, model downloads, and embedding caches remain
  disabled.
- Phase 3A deterministic local visual-smoke diagnostics exist for the
  synthetic smoke `dev` split, including manifest-backed page-image loading, a
  hashed patch-token late-interaction-style smoke scorer, and diagnostic report
  generation.
- The active `add-mvp-retrieval-pipeline` worktree adds a diagnostic MVP
  command,
  `PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json`, that
  composes fixed synthetic smoke manifests, explicit `evaluated_split_pages`
  candidate-universe metadata, text baselines, and a deterministic CPU-only
  `mock_visual` late-interaction scaffold with MaxSim and mock cache evidence.
  This MVP is diagnostic/smoke evidence only and is not archived unless a future
  closeout explicitly archives the OpenSpec change.

Do not add real visual-model retrieval, ColPali/ColQwen inference, external
image embeddings, real model embedding caches, hard-negative mining outputs, LoRA/QLoRA,
training scripts, adapters, checkpoints, final test evaluation, benchmark
result tables, retrieval improvement claims, model superiority claims,
frozen-test performance claims, chatbot UI, generic RAG app behavior,
Agent/browser automation positioning, citation safety systems, production RAG
deployment, or QA generation without a future accepted OpenSpec change.

## Validation Baseline

Run these commands from the repository root for local validation:

```bash
pytest -q
ruff check .
mypy src
openspec validate --all --strict
```

Validation must remain local-only and CPU-only. Do not require network access,
GPU hardware, model downloads, external embedding services, final test data, or
unreviewed benchmark surfaces unless a future OpenSpec change explicitly adds
that contract.
