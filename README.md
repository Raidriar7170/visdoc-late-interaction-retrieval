# VisDoc-Retrieve

VisDoc-Retrieve is a page-level multimodal document retrieval and ranking
project for visually rich PDFs and scanned documents. The intended algorithmic
path is to compare OCR/text baselines with visual late-interaction retrieval,
then evaluate hard-negative mining and future LoRA adaptation under a frozen
benchmark contract.

**Current status:** Phase 1 data format and deterministic synthetic smoke corpus
are available. No final benchmark results exist yet, and this repository does
not claim retrieval improvement, model superiority, or frozen-test performance.

This repository currently contains the project skeleton, local validation
configuration, Phase 1 page/query manifest validation, and a small generated
synthetic technical page corpus under `data/synthetic-smoke/`. It does not yet
contain retrieval implementations, ranking metrics, ColPali/ColQwen inference,
embedding caches, training scripts, adapters, checkpoints, benchmark reports, or
final result tables.

## Project Boundary

The project is about document retrieval and ranking, not a chatbot UI, generic
RAG app, Agent workflow, browser automation system, citation safety layer,
production RAG deployment, or QA generation pipeline.

Future OpenSpec phases may introduce the missing data, retrieval, evaluation,
and training surfaces only after their contracts are proposed and reviewed.

## Local Validation

The local validation baseline is intentionally CPU-only and local-only:

```bash
pytest -q
ruff check .
mypy src
openspec validate --all --strict
```

The tests import the package and validate the synthetic corpus without network
access, GPU hardware, model downloads, or external services.
