# VisDoc Evidence Index

This index maps the current public evidence for VisDoc-Retrieve after the
Phase 6D one-time frozen final comparison and Phase 7A final presentation
package.

## Claim Boundaries

- Final benchmark: one-time frozen final comparison completed in Phase 6D.
- Final test evaluation: read once under `phase-6b-final-comparison-protocol/v1`.
- No-retune pledge: active after Phase 6D.
- Benchmark improvement claim: not supported; claim status is
  `no_clear_improvement_claim`.
- Model weights committed: no.
- Adapter checkpoints committed: no.
- Training caches committed: no.
- Private local config or exact private model path committed: no.
- `max_steps=1` / `sample_limit=1` tiny runner proof: pipeline proof only, not
  model performance.
- Phase 5K dev-only evaluation harness: dev-only sanity/schema evidence, not
  final test or final benchmark.
- `mock_visual`: deterministic MaxSim scaffold only, not real visual-model
  performance.
- `tiny_lora_adapter` and `zero_shot_visual_backend`: final status is
  `not_available`; metrics were not fabricated.

## Milestone Evidence

### Synthetic Corpus And Manifests

Status: materialized local synthetic smoke corpus with page/query manifests.

Evidence: `data/synthetic-smoke/summary.json`,
`data/synthetic-smoke/pages.jsonl`, `data/synthetic-smoke/queries.jsonl`,
`docs/human-briefs/2026-06-28-add-data-format-and-synthetic-corpus.html`,
`openspec/changes/archive/2026-06-27-add-data-format-and-synthetic-corpus/`.

### Text Baselines And Candidate Universe

Status: deterministic BM25, lexical cosine, local-stub neural text, and RRF
diagnostics with explicit candidate-universe metadata.

Evidence: `reports/text-baselines-synthetic-smoke.json`,
`configs/text-baselines-synthetic-smoke.json`,
`docs/human-briefs/2026-06-29-add-neural-text-baseline-and-candidate-universe.html`,
`openspec/changes/archive/2026-06-29-add-neural-text-baseline-and-candidate-universe/`.

### Diagnostic MVP Pipeline

Status: one-command diagnostic pipeline over dev split with mock visual MaxSim
scaffold.

Evidence: `reports/mvp/metrics.json`, `reports/mvp/rankings.csv`,
`reports/mvp/mock-visual-embeddings.json`, `reports/mvp/run-card.md`,
`docs/human-briefs/2026-06-30-visdoc-mvp.html`.

### Optional Visual Backend Scaffold

Status: import-safe optional local visual backend and cache schema; not default
MVP backend.

Evidence: `reports/visual-baselines-synthetic-smoke.json`,
`docs/human-briefs/2026-06-30-visual-zero-shot-backend.html`,
`openspec/changes/archive/2026-07-07-add-visual-zero-shot-backend/`.

### Hard-Negative Mining

Status: train/dev hard-negative artifacts generated from diagnostic surfaces;
final test not used.

Evidence: `data/derived/hard_negatives/train.jsonl`,
`data/derived/hard_negatives/dev.jsonl`,
`reports/hard-negatives/mining-summary.json`,
`reports/hard-negatives/leakage-check.json`,
`reports/hard-negatives/run-card.md`,
`docs/human-briefs/2026-07-01-hard-negative-mining.html`.

### Training Readiness

Status: dry-run readiness package and safety checks; no model download, GPU use,
training, or adapter checkpoint.

Evidence: `reports/training-readiness/artifact-freeze.json`,
`reports/training-readiness/dataset-summary.json`,
`reports/training-readiness/safety-check.json`,
`reports/training-readiness/dry-run-card.md`,
`docs/human-briefs/2026-07-01-training-readiness.md`.

### Pilot Launch And Backend Wiring Gates

Status: gated pilot launcher and backend wiring evidence; default path remains
blocked unless safety gates pass.

Evidence: `reports/training-pilot/environment-check.json`,
`reports/training-pilot/blocked-run-card.md`,
`reports/training-pilot/safety-check.json`,
`reports/training-pilot/dev-eval-schema.json`,
`reports/training-pilot/phase-5d-environment-check.json`,
`reports/training-pilot/phase-5d-blocked-run-card.md`,
`docs/human-briefs/2026-07-01-training-pilot-launch-gate.html`,
`docs/human-briefs/2026-07-01-real-training-backend-wiring.html`.

### A100 Gate Evidence

Status: runtime, dependency, and model-path gates recorded as evidence; no final
benchmark and no committed private path.

Evidence: `reports/training-pilot/phase-5e-a100-preflight.json`,
`reports/training-pilot/phase-5f-runtime-gates.json`,
`reports/training-pilot/phase-5g-runtime-gate-closure.json`,
`reports/training-pilot/phase-5h-model-path-gate-closure.json`,
`docs/human-briefs/2026-07-02-a100-real-training-preflight.html`,
`docs/human-briefs/2026-07-03-a100-runtime-gate-materialization.html`,
`docs/human-briefs/2026-07-04-a100-runtime-gate-closure.html`,
`docs/human-briefs/2026-07-04-a100-model-path-gate-closure.html`.

### Phase 5I Blocked Tiny Pilot Attempt

Status: gated tiny pilot attempt failed closed; no training result or adapter
committed.

Evidence: `reports/training-pilot/phase-5i-environment-check.json`,
`reports/training-pilot/phase-5i-blocked-run-card.md`,
`reports/training-pilot/phase-5i-safety-check.json`,
`reports/training-pilot/phase-5i-dev-eval.json`,
`reports/training-pilot/phase-5i-adapter-manifest.sanitized.json`,
`docs/human-briefs/2026-07-05-gated-tiny-real-pilot.html`,
`openspec/changes/archive/2026-07-06-run-phase-5i-gated-tiny-real-pilot/`.

### Phase 5J Reviewed Tiny Runner Proof

Status: reviewed A100 tiny LoRA backend runner proof with `max_steps=1` and
`sample_limit=1`; not a benchmark.

Evidence: `reports/training-pilot/phase-5j-environment-check.json`,
`reports/training-pilot/phase-5j-pilot-run-card.md`,
`reports/training-pilot/phase-5j-safety-check.json`,
`reports/training-pilot/phase-5j-dev-eval.json`,
`reports/training-pilot/phase-5j-adapter-manifest.sanitized.json`,
`docs/human-briefs/2026-07-06-reviewed-a100-tiny-lora-runner.html`,
`openspec/changes/archive/2026-07-06-add-reviewed-a100-tiny-lora-backend-runner/`.

### Phase 5K Dev-Only Evaluation Harness

Status: dev-only evaluation harness records comparison schema and
missing-adapter status without final-test use or fabricated metrics.

Evidence: `reports/training-pilot/phase-5k-environment-check.json`,
`reports/training-pilot/phase-5k-safety-check.json`,
`reports/training-pilot/phase-5k-blocked-run-card.md`,
`reports/training-pilot/phase-5k-adapter-manifest.sanitized.json`,
`reports/training-pilot/phase-5k-dev-only-eval.json`,
`reports/training-pilot/phase-5k-comparison-schema.json`,
`docs/human-briefs/2026-07-06-dev-only-pilot-evaluation.html`,
`openspec/specs/dev-only-pilot-evaluation-harness/spec.md`,
`openspec/changes/archive/2026-07-06-add-dev-only-pilot-evaluation-harness/`.

### Phase 6B Final-Comparison Protocol Freeze

Status: final-comparison protocol, comparison schema, and public claim
checklist are frozen without final-test use or benchmark claims.

Evidence: `docs/final-comparison-protocol.md`,
`reports/final-comparison-protocol/phase-6b-protocol-freeze.json`,
`reports/final-comparison-protocol/phase-6b-comparison-schema.json`,
`reports/final-comparison-protocol/phase-6b-claim-checklist.json`,
`docs/human-briefs/2026-07-07-final-comparison-protocol-freeze.html`,
`openspec/changes/archive/2026-07-07-freeze-final-comparison-protocol/`.

### Phase 6C Final-Comparison Execution Gate Dry Run

Status: final-comparison execution gate and dry-run readiness evidence recorded;
final test was not read and final comparison was not executed in this phase.

Evidence: `reports/final-comparison-protocol/phase-6c-execution-gate-dry-run.json`,
`reports/final-comparison-protocol/phase-6c-readiness-report.md`,
`reports/final-comparison-protocol/phase-6c-claim-checklist.json`,
`docs/human-briefs/2026-07-08-final-comparison-dry-run-gate.md`,
`openspec/changes/archive/2026-07-08-add-final-comparison-execution-gate-dry-run/`.

### Phase 6D One-Time Frozen Final Comparison

Status: final comparison completed exactly once under the frozen protocol.
Final test was read once. No training, tuning, A100/GPU/SSH, model download,
retrieval behavior change, metric-definition change, candidate-universe change,
or result-driven rerun occurred.

Systems run: `bm25`, `lexical_cosine`, `bm25_lexical_rrf`, and `mock_visual`.

Systems not available: `tiny_lora_adapter` and `zero_shot_visual_backend`.

Claim boundary: `reports/final-comparison/final-claim-checklist.json` records
`benchmark_claim_allowed=false` and `claim_status=no_clear_improvement_claim`.

Evidence: `reports/final-comparison/final-comparison-run-manifest.json`,
`reports/final-comparison/final-metrics.json`,
`reports/final-comparison/final-rankings.csv`,
`reports/final-comparison/final-comparison-report.md`,
`reports/final-comparison/final-claim-checklist.json`,
`reports/final-comparison/no-retune-pledge.md`,
`docs/human-briefs/2026-07-08-final-comparison-report.md`,
`openspec/changes/archive/2026-07-08-run-one-time-frozen-final-comparison/`.

### Phase 7A Final Presentation Package

Status: final presentation package prepared for review. This phase does not
rerun final comparison, read or modify final labels/qrels, train, tune, modify
final metrics, modify final rankings, or make an unsupported improvement claim.

Evidence: `README.md`, `docs/project-card.md`, `docs/resume-bullets.md`,
`docs/interview-talking-points.md`, `docs/evidence-index.md`,
`docs/human-briefs/2026-07-08-add-final-presentation-package.html`,
`openspec/changes/archive/2026-07-08-add-final-presentation-package/`.

### Phase 7B v0.1 Release Preparation

Status: release-preparation package prepared for review. This phase does not
create a tag, publish a GitHub Release, deploy, rerun final comparison, read
final labels/qrels, train, tune, modify final metrics, modify final rankings,
or add an unsupported improvement claim.

Evidence: `CHANGELOG.md`, `docs/release/v0.1.0-release-notes.md`,
`docs/release/v0.1.0-tag-checklist.md`,
`reports/release/v0.1.0-release-readiness.json`,
`docs/human-briefs/2026-07-08-prepare-v0-1-final-release.html`,
`openspec/changes/prepare-v0-1-final-release/`.

## Validation Surface

The current local validation bundle for this milestone narrative phase is:

```bash
PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json
PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives --config configs/hard_negatives.json
PYTHONPATH=src python -m visdoc_retrieve.train_lora_dry_run --config configs/train_lora_dry_run.json
PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot --config configs/train_lora_pilot.local.example.json || test $? -eq 2
python -m py_compile src/visdoc_retrieve/*.py
pytest -q
ruff check .
mypy src
openspec validate --all --strict
git diff --check
```

The pilot command is expected to remain blocked by default safety gates unless
an explicit local training configuration and environment are supplied. This
documentation checkpoint does not supply those inputs.
