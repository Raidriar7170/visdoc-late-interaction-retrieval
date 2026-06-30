# VisDoc-Retrieve

VisDoc-Retrieve is a page-level multimodal document retrieval
and ranking project for visually rich PDFs
and scanned documents.
The intended algorithmic path is to compare OCR/text baselines
with visual late-interaction retrieval,
then evaluate hard-negative mining
and future LoRA adaptation under a frozen benchmark contract.

**Current status:** Phase 3A diagnostic baselines remain available,
with a Phase 2.5 text/candidate-universe clarification applied
to the synthetic smoke development split,
and an active diagnostic MVP pipeline change in this worktree:
Phase 2 text-only baselines, explicit candidate-universe metadata,
a deterministic local visual-smoke report,
and a one-command MVP evidence bundle.
No final benchmark results exist yet,
and this repository does not claim retrieval improvement,
model superiority, or frozen-test performance.

This repository currently contains the project skeleton,
local validation configuration,
Phase 1 page/query manifest validation,
and a small generated synthetic technical page corpus
under `data/synthetic-smoke/`.
It also contains deterministic BM25, local lexical cosine,
a config-gated local-stub neural text baseline,
BM25+lexical RRF, and BM25+neural RRF text diagnostics
plus a diagnostic report runner.
It also contains a deterministic local visual-smoke runner
over existing page image artifacts.
The MVP command composes a bounded subset of those surfaces with a
deterministic mock visual late-interaction scaffold and MaxSim scoring.
It does not contain ColPali/ColQwen inference,
external embedding caches, training scripts,
adapters, checkpoints,
final benchmark reports, or final result tables.

## Project Boundary

The project is about document retrieval and ranking,
not a chatbot UI, generic RAG app, Agent workflow,
browser automation system, citation safety layer,
production RAG deployment,
or QA generation pipeline.

Future OpenSpec phases may introduce the missing data,
retrieval, evaluation, and training surfaces only after
their contracts are proposed and reviewed.

## Local Validation

The local validation baseline is intentionally CPU-only
and local-only:

```bash
pytest -q
ruff check .
mypy src
openspec validate --all --strict
```

The tests import the package and validate the synthetic corpus
without network access, GPU hardware, model downloads,
or external services.

Generate the text-only diagnostic report
from the repository root with:

```bash
PYTHONPATH=src python -m visdoc_retrieve.text_baseline_report configs/text-baselines-synthetic-smoke.json
```

The default config evaluates only the synthetic smoke `dev` split
against the `evaluated_split_pages` candidate universe:
24 dev queries ranked over 8 dev pages.
It records the final `test` split as `not_run`.
The `neural_text` method uses a deterministic local stub provider
with external embeddings, network, GPU, model downloads,
and embedding caches disabled.

Generate the deterministic local visual-smoke diagnostic report with:

```bash
PYTHONPATH=src python -m visdoc_retrieve.visual_baseline_report configs/visual-baselines-synthetic-smoke.json --repo-root .
```

The visual-smoke report evaluates only the synthetic smoke `dev` split,
records the final `test` split as `not_run`,
and explicitly disables network, GPU, external model downloads,
training, hard-negative output, and benchmark claims.

Run the diagnostic MVP pipeline from a clean checkout with:

```bash
PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json
```

The MVP uses `data/synthetic-smoke/pages.jsonl` and
`data/synthetic-smoke/queries.jsonl`, evaluates 24 `dev` queries over the
`evaluated_split_pages` candidate universe of 8 `dev` pages, and writes:

- `reports/mvp/metrics.json`
- `reports/mvp/rankings.csv`
- `reports/mvp/mock-visual-embeddings.json`
- `reports/mvp/run-card.md`
- `docs/human-briefs/2026-06-30-visdoc-mvp.html`

Default MVP methods are `bm25`, `lexical_cosine`, `bm25_lexical_rrf`, and
`mock_visual`. The `mock_visual` path is a deterministic CPU-only scaffold with
MaxSim scoring and cache round-trip evidence; it is not real ColPali or ColQwen
execution. MVP metrics are diagnostic smoke evidence only and must not be read
as final benchmark, model-superiority, frozen-test, or retrieval-improvement
claims.
