# Configs

This directory contains OpenSpec-managed local configuration.

## Text Baselines

- `text-baselines-synthetic-smoke.json` generates the Phase 2.5 text-only
  diagnostic report at `reports/text-baselines-synthetic-smoke.json`.
- Candidate universe: `evaluated_split_pages`.
- Evaluated split: `dev`.
- Ranked candidate pages: 8 dev pages.
- Final `test` split: recorded as `not_run`.
- Enabled methods: `bm25`, deterministic local `lexical_cosine`,
  deterministic local-stub `neural_text`, `bm25_lexical_rrf`, and
  `bm25_neural_rrf`.
- External embeddings, FAISS, network downloads, GPU execution, model
  downloads, embedding caches, visual inference, hard-negative mining, final
  test evaluation, and training are disabled by default.

## Visual Smoke Baselines

- `visual-baselines-synthetic-smoke.json` generates the Phase 3A deterministic
  local visual-smoke diagnostic report at
  `reports/visual-baselines-synthetic-smoke.json`.
- Enabled method: `visual_smoke`.
- Evaluated split: `dev`.
- Final `test` split: recorded as `not_run`.
- ColPali/ColQwen inference, external model downloads, network access, GPU
  execution, hard-negative output, benchmark claims, and training are disabled.
