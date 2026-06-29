# VisDoc-Retrieve

VisDoc-Retrieve is a page-level multimodal document retrieval and ranking
project for visually rich PDFs and scanned documents. The intended algorithmic
path is to compare OCR/text baselines with visual late-interaction retrieval,
then evaluate hard-negative mining and future LoRA adaptation under a frozen
benchmark contract.

**Current status:** Phase 3A diagnostic baselines are available for the
synthetic smoke development split: Phase 2 text-only baselines plus a
deterministic local visual-smoke report. No final benchmark results exist yet,
and this repository does not claim retrieval improvement, model superiority, or
frozen-test performance.

This repository currently contains the project skeleton, local validation
configuration, Phase 1 page/query manifest validation, and a small generated
synthetic technical page corpus under `data/synthetic-smoke/`. It also contains
deterministic BM25, local dense-text, and hybrid/RRF text baselines plus a
diagnostic report runner. It also contains a deterministic local visual-smoke
runner over existing page image artifacts. It does not contain ColPali/ColQwen
inference, embedding caches, training scripts, adapters, checkpoints, final
benchmark reports, or final result tables.

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

Generate the text-only diagnostic report from the repository root with:

```bash
PYTHONPATH=src python -m visdoc_retrieve.text_baseline_report configs/text-baselines-synthetic-smoke.json
```

The default config evaluates only the synthetic smoke `dev` split and records
the final `test` split as `not_run`.

Generate the deterministic local visual-smoke diagnostic report with:

```bash
PYTHONPATH=src python -m visdoc_retrieve.visual_baseline_report configs/visual-baselines-synthetic-smoke.json --repo-root .
```

The visual-smoke report evaluates only the synthetic smoke `dev` split, records
the final `test` split as `not_run`, and explicitly disables network, GPU,
external model downloads, training, hard-negative output, and benchmark claims.
