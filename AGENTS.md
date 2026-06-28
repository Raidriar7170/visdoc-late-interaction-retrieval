# Repository Agent Instructions

OpenSpec is the durable source of truth for scoped changes in this repository.
When `openspec/config.yaml` is present, use the relevant OpenSpec proposal,
design, specs, and tasks before implementing non-trivial changes.

## Phase 0 Boundary

Phase 0 may contain only the repository skeleton, package metadata, import-only
smoke validation, documentation placeholders, and a bounded progress ledger.

Do not add data generation, page rendering, OCR extraction, manifest schemas,
retrieval datasets, BM25, dense or hybrid retrieval, retrieval metrics,
ColPali/ColQwen inference, embedding caches, hard-negative mining, LoRA/QLoRA,
training scripts, adapters, checkpoints, benchmark reports, final result
tables, chatbot UI, generic RAG app behavior, Agent/browser automation
positioning, citation safety systems, production RAG deployment, or QA
generation without a future accepted OpenSpec change.

## Validation Baseline

Run these commands from the repository root for Phase 0 validation:

```bash
pytest -q
ruff check .
mypy src
openspec validate --all --strict
```

Smoke tests must remain local-only and import-only until a later OpenSpec change
adds data, retrieval, model, or evaluation contracts.
