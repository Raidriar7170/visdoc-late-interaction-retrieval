# Configs

This directory contains OpenSpec-managed local configuration.

## Text Baselines

- `text-baselines-synthetic-smoke.json` generates the Phase 2 text-only
  diagnostic report at `reports/text-baselines-synthetic-smoke.json`.
- Enabled methods: BM25, deterministic local dense-text, and hybrid/RRF.
- Evaluated split: `dev`.
- Final `test` split: recorded as `not_run`.
- External embeddings, FAISS, network downloads, GPU execution, visual
  inference, hard-negative mining, and training are disabled by default.
