## 1. OpenSpec And Opsx Phase Surface

- [x] 1.1 Create Phase 5D proposal, design, spec, and task artifacts for real backend wiring.
- [x] 1.2 Validate the Phase 5D OpenSpec change with strict validation before implementation.
- [x] 1.3 Refresh `.opsx-goal.yaml` and bounded inbox phase evidence so the practical goal matches Phase 5D instead of stale MVP wording.

## 2. Tests First

- [x] 2.1 Add RED tests that top-level imports do not require torch, transformers, peft, colpali_engine, or the backend module.
- [x] 2.2 Add RED tests for `allow_real_training=false`, missing local model path, `allow_final_test=true`, CUDA unavailable, missing optional dependencies, `max_steps > 20`, and `sample_limit > 8`.
- [x] 2.3 Add RED tests for ignored adapter output, train-only sample limiting, no final-test reads, environment-check schema, safety-check schema, blocked run-card generation, and Phase 5D report naming.
- [x] 2.4 Add RED tests that existing MVP, hard-negative mining, Phase 5A dry-run, and Phase 5B/5C blocked pilot CLI behavior remain valid.

## 3. Backend Wiring

- [x] 3.1 Add `src/visdoc_retrieve/lora_training_backend.py` with no top-level optional ML imports and a guarded local-only backend entry point.
- [x] 3.2 Extend pilot config parsing with `sample_limit`, `backend_dependency`, and Phase 5D output fields while preserving the default blocked example.
- [x] 3.3 Enforce all real-training gates before backend execution, including sample-limit, local model path, CUDA, optional dependency, final-test, and ignored-output gates.
- [x] 3.4 Build the tiny train sample from train hard negatives only, cap it at at most 8 triples, and keep dev usage limited to schema/sanity metadata.
- [x] 3.5 Route all model loading through local paths with local-files-only behavior and no remote model fallback or download behavior.

## 4. Evidence Outputs

- [x] 4.1 Add or update `configs/train_lora_pilot.local.example.json` for Phase 5D fields and safe defaults.
- [x] 4.2 Generate Phase 5D environment check, safety check, blocked/pilot run-card, sanitized adapter manifest, and dev-eval evidence under `reports/training-pilot/`.
- [x] 4.3 Generate `docs/human-briefs/2026-07-01-real-training-backend-wiring.html` and update `reports/progress-ledger.yaml` with Phase 5D status.
- [x] 4.4 Update `.gitignore` only if needed and verify model weights, adapters, checkpoints, caches, logs, `.worktrees`, private paths, final-test metrics, and benchmark claims are not committed.

## 5. Validation, Review, And PR

- [x] 5.1 Run the required MVP, hard-negative mining, Phase 5A dry-run, Phase 5D pilot command, py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check` commands.
- [x] 5.2 Run a Reviewer subagent over the diff and fix Must Fix items only unless replanning is required.
- [x] 5.3 Commit, push `codex/phase-5d-real-training-backend-wiring`, create a PR, and stop without merge, deploy, or OpenSpec archive.
