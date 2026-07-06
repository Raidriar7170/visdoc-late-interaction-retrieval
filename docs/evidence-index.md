# VisDoc Evidence Index

This index maps the current public evidence for VisDoc-Retrieve after the
Phase 5K dev-only pilot evaluation harness was merged and archived.

## Claim Boundaries

- Final benchmark: not run.
- Final test evaluation: not used.
- Benchmark improvement claim: none.
- Model weights committed: no.
- Adapter checkpoints committed: no.
- Training caches committed: no.
- Private local config or exact private model path committed: no.
- `max_steps=1` / `sample_limit=1` tiny runner proof: pipeline proof only, not
  model performance.
- Phase 5K dev-only evaluation harness: dev-only sanity/schema evidence, not
  final test or final benchmark.

## Milestone Evidence

| Area | Current status | Evidence |
| --- | --- | --- |
| Synthetic corpus and manifests | Materialized local synthetic smoke corpus with page/query manifests | `data/synthetic-smoke/summary.json`, `data/synthetic-smoke/pages.jsonl`, `data/synthetic-smoke/queries.jsonl`, `docs/human-briefs/2026-06-28-add-data-format-and-synthetic-corpus.html`, `openspec/changes/archive/2026-06-27-add-data-format-and-synthetic-corpus/` |
| Text baselines and candidate universe | Deterministic BM25, lexical cosine, local-stub neural text, and RRF diagnostics with explicit candidate-universe metadata | `reports/text-baselines-synthetic-smoke.json`, `configs/text-baselines-synthetic-smoke.json`, `docs/human-briefs/2026-06-29-add-neural-text-baseline-and-candidate-universe.html`, `openspec/changes/archive/2026-06-29-add-neural-text-baseline-and-candidate-universe/` |
| Diagnostic MVP pipeline | One-command diagnostic pipeline over dev split with mock visual MaxSim scaffold | `reports/mvp/metrics.json`, `reports/mvp/rankings.csv`, `reports/mvp/mock-visual-embeddings.json`, `reports/mvp/run-card.md`, `docs/human-briefs/2026-06-30-visdoc-mvp.html` |
| Optional visual backend scaffold | Import-safe optional local visual backend and cache schema; not default MVP backend | `reports/visual-baselines-synthetic-smoke.json`, `docs/human-briefs/2026-06-30-visual-zero-shot-backend.html`, `openspec/changes/add-visual-zero-shot-backend/` |
| Hard-negative mining | Train/dev hard-negative artifacts generated from diagnostic surfaces; final test not used | `data/derived/hard_negatives/train.jsonl`, `data/derived/hard_negatives/dev.jsonl`, `reports/hard-negatives/mining-summary.json`, `reports/hard-negatives/leakage-check.json`, `reports/hard-negatives/run-card.md`, `docs/human-briefs/2026-07-01-hard-negative-mining.html` |
| Training readiness | Dry-run readiness package and safety checks; no model download, GPU use, training, or adapter checkpoint | `reports/training-readiness/artifact-freeze.json`, `reports/training-readiness/dataset-summary.json`, `reports/training-readiness/safety-check.json`, `reports/training-readiness/dry-run-card.md`, `docs/human-briefs/2026-07-01-training-readiness.md` |
| Pilot launch and backend wiring gates | Gated pilot launcher and backend wiring evidence; default path remains blocked unless safety gates pass | `reports/training-pilot/environment-check.json`, `reports/training-pilot/blocked-run-card.md`, `reports/training-pilot/safety-check.json`, `reports/training-pilot/dev-eval-schema.json`, `reports/training-pilot/phase-5d-environment-check.json`, `reports/training-pilot/phase-5d-blocked-run-card.md`, `docs/human-briefs/2026-07-01-training-pilot-launch-gate.html`, `docs/human-briefs/2026-07-01-real-training-backend-wiring.html` |
| A100 gate evidence | Runtime, dependency, and model-path gates recorded as evidence; no final benchmark and no committed private path | `reports/training-pilot/phase-5e-a100-preflight.json`, `reports/training-pilot/phase-5f-runtime-gates.json`, `reports/training-pilot/phase-5g-runtime-gate-closure.json`, `reports/training-pilot/phase-5h-model-path-gate-closure.json`, `docs/human-briefs/2026-07-02-a100-real-training-preflight.html`, `docs/human-briefs/2026-07-03-a100-runtime-gate-materialization.html`, `docs/human-briefs/2026-07-04-a100-runtime-gate-closure.html`, `docs/human-briefs/2026-07-04-a100-model-path-gate-closure.html` |
| Phase 5I blocked tiny pilot attempt | Gated tiny pilot attempt failed closed; no training result or adapter committed | `reports/training-pilot/phase-5i-environment-check.json`, `reports/training-pilot/phase-5i-blocked-run-card.md`, `reports/training-pilot/phase-5i-safety-check.json`, `reports/training-pilot/phase-5i-dev-eval.json`, `reports/training-pilot/phase-5i-adapter-manifest.sanitized.json`, `docs/human-briefs/2026-07-05-gated-tiny-real-pilot.html`, `openspec/changes/archive/2026-07-06-run-phase-5i-gated-tiny-real-pilot/` |
| Phase 5J reviewed tiny runner proof | Reviewed A100 tiny LoRA backend runner proof with `max_steps=1` and `sample_limit=1`; not a benchmark | `reports/training-pilot/phase-5j-environment-check.json`, `reports/training-pilot/phase-5j-pilot-run-card.md`, `reports/training-pilot/phase-5j-safety-check.json`, `reports/training-pilot/phase-5j-dev-eval.json`, `reports/training-pilot/phase-5j-adapter-manifest.sanitized.json`, `docs/human-briefs/2026-07-06-reviewed-a100-tiny-lora-runner.html`, `openspec/changes/archive/2026-07-06-add-reviewed-a100-tiny-lora-backend-runner/` |
| Phase 5K dev-only evaluation harness | Dev-only evaluation harness records comparison schema and missing-adapter status without final-test use or fabricated metrics | `reports/training-pilot/phase-5k-environment-check.json`, `reports/training-pilot/phase-5k-safety-check.json`, `reports/training-pilot/phase-5k-blocked-run-card.md`, `reports/training-pilot/phase-5k-adapter-manifest.sanitized.json`, `reports/training-pilot/phase-5k-dev-only-eval.json`, `reports/training-pilot/phase-5k-comparison-schema.json`, `docs/human-briefs/2026-07-06-dev-only-pilot-evaluation.html`, `openspec/specs/dev-only-pilot-evaluation-harness/spec.md`, `openspec/changes/archive/2026-07-06-add-dev-only-pilot-evaluation-harness/` |

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
