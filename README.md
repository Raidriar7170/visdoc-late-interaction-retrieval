# VisDoc-Retrieve

VisDoc-Retrieve is a page-level multimodal document retrieval
and ranking project for visually rich PDFs
and scanned documents.
The intended algorithmic path is to compare OCR/text baselines
with visual late-interaction retrieval,
then evaluate hard-negative mining
and future LoRA adaptation under a frozen benchmark contract.

**Current status:** Phase 6D has completed the one-time frozen final comparison
under `phase-6b-final-comparison-protocol/v1`, and the no-retune pledge is now
active. The final test split has been read for that authorized run, and no
tuning, retrieval-pipeline change, metric-definition change, candidate-universe
change, final-label change, or result-driven rerun is allowed after it.

The final claim checklist records `no_clear_improvement_claim`. The repository
can demonstrate a reproducible retrieval/evaluation pipeline and a disciplined
final-comparison process, but it does not claim benchmark improvement, model
superiority, or production training readiness. The final run executed
deterministic `bm25`, `lexical_cosine`, `bm25_lexical_rrf`, and `mock_visual`
systems. `tiny_lora_adapter` and `zero_shot_visual_backend` were reported as
`not_available`; their metrics were not fabricated.

The `mock_visual` row remains a deterministic CPU-only MaxSim scaffold, not
real visual-model performance. The `max_steps=1` / `sample_limit=1` tiny A100
LoRA runner proof remains pipeline evidence, not benchmark performance or
formal training gain. No model weights, adapter checkpoints, training caches,
private local configs, or exact private model paths are committed.

This repository currently contains the project skeleton, local validation
configuration, Phase 1 page/query manifest validation, and a small generated
synthetic technical page corpus under `data/synthetic-smoke/`. It also
contains deterministic BM25, local lexical cosine, a config-gated local-stub
neural text baseline, BM25+lexical RRF, and BM25+neural RRF text diagnostics
plus a diagnostic report runner. The MVP command composes a bounded subset of
those surfaces with a deterministic mock visual late-interaction scaffold and
MaxSim scoring. Later phases add optional local-only visual backend wiring,
hard-negative mining, training-readiness dry-runs, gated pilot launch safety,
and A100 evidence gates without turning those surfaces into final benchmark
claims.

For a path-by-path map of the current evidence, see
[`docs/evidence-index.md`](docs/evidence-index.md). For a recruiter-facing
project card, see [`docs/project-card.md`](docs/project-card.md). For resume
phrasing, see [`docs/resume-bullets.md`](docs/resume-bullets.md). For interview
preparation, see
[`docs/interview-talking-points.md`](docs/interview-talking-points.md).
For the Phase 7A Human Brief, see
[`docs/human-briefs/2026-07-08-add-final-presentation-package.html`](docs/human-briefs/2026-07-08-add-final-presentation-package.html).
For the frozen final-comparison protocol, see
[`docs/final-comparison-protocol.md`](docs/final-comparison-protocol.md).
For the final comparison report and claim boundary, see
[`reports/final-comparison/final-comparison-report.md`](reports/final-comparison/final-comparison-report.md)
and
[`reports/final-comparison/final-claim-checklist.json`](reports/final-comparison/final-claim-checklist.json).
For `v0.1.0` release-preparation materials, see
[`CHANGELOG.md`](CHANGELOG.md),
[`docs/release/v0.1.0-release-notes.md`](docs/release/v0.1.0-release-notes.md),
[`docs/release/v0.1.0-tag-checklist.md`](docs/release/v0.1.0-tag-checklist.md),
and
[`reports/release/v0.1.0-release-readiness.json`](reports/release/v0.1.0-release-readiness.json).

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
