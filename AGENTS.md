# Repository Agent Instructions

OpenSpec is the durable source of truth for scoped changes in this repository.
When `openspec/config.yaml` is present, use the relevant OpenSpec proposal,
design, specs, and tasks before implementing non-trivial changes.

## Current Phase Boundary

The repository is currently through Phase 2:

- Phase 1 synthetic corpus and manifest validation exist under
  `data/synthetic-smoke/` and `src/visdoc_retrieve/data_schema.py`.
- Phase 2 text-only diagnostic baselines exist for the synthetic smoke `dev`
  split, including deterministic BM25, local dense-text, hybrid/RRF, metrics,
  and diagnostic report generation.

Do not add visual retrieval, ColPali/ColQwen inference, image embeddings,
embedding caches, hard-negative mining outputs, LoRA/QLoRA, training scripts,
adapters, checkpoints, final test evaluation, benchmark result tables,
retrieval improvement claims, model superiority claims, frozen-test performance
claims, chatbot UI, generic RAG app behavior, Agent/browser automation
positioning, citation safety systems, production RAG deployment, or QA
generation without a future accepted OpenSpec change.

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
