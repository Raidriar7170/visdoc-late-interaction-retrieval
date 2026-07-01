## 1. OpenSpec Phase Surface

- [x] 1.1 Create proposal, design, specs, and tasks for Phase 5B training pilot launch gate.
- [x] 1.2 Validate the new OpenSpec change with strict validation before implementation.

## 2. Tests First

- [x] 2.1 Add RED tests for pilot config parsing, required fields, `allow_real_training=false` blocked behavior, `allow_final_test=true` hard failure, and max-step budget rejection.
- [x] 2.2 Add RED tests for missing local model path blocking, CUDA unavailable blocking, environment-check JSON shape, blocked run-card generation, and optional-import guarding.
- [x] 2.3 Add RED tests for dev-only evaluation schema, final-test path rejection, adapter manifest example generation, and safety-check content.
- [x] 2.4 Add RED tests for adapter/model/checkpoint/cache ignore rules and preservation of MVP, hard-negative mining, and Phase 5A dry-run CLIs.

## 3. Pilot Gate Implementation

- [x] 3.1 Add `configs/train_lora_pilot.local.example.json` with model identity, local model path, adapter output, hard-negative inputs, corpus/query/qrels inputs, candidate universe, loss, LoRA/QLoRA, batch, budget, seed, device, training/final-test flags, adapter save flag, and report paths.
- [x] 3.2 Add pilot config dataclasses/loading, strict type/path validation, `allow_final_test=false` enforcement, tiny max-step enforcement, and ignored adapter-output validation.
- [x] 3.3 Add environment gate checks for config permission, `VISDOC_ENABLE_REAL_TRAINING=1`, local model path existence, CUDA availability, budget, ignored output path, and pilot/dev-only run-card wording.
- [x] 3.4 Add `visdoc_retrieve.train_lora_pilot` CLI that writes environment-check and blocked run-card evidence by default, returns clear blocked exit code `2`, and routes to real training only when all gates pass.
- [x] 3.5 Add guarded real-training launcher scaffold with optional torch/transformers/peft/colpali imports only inside the real pilot function and no remote model download behavior.

## 4. Evidence Outputs

- [x] 4.1 Emit `reports/training-pilot/environment-check.json`, `blocked-run-card.md` or `pilot-run-card.md`, and `safety-check.json` from the CLI.
- [x] 4.2 Emit `reports/training-pilot/dev-eval-schema.json` with dev-only scope, `status=not_run`, null metrics when no adapter exists, and `final_test_used=false`.
- [x] 4.3 Emit `reports/training-pilot/adapter-manifest.example.json` with adapter output directory, model identity, hard-negative/config hashes, git commit, max steps, seed, device, final-test exclusion, created timestamp, and pilot status.
- [x] 4.4 Update `.gitignore`, `reports/progress-ledger.yaml`, and `docs/human-briefs/2026-07-01-training-pilot-launch-gate.html` without committing model weights, adapters, checkpoints, caches, final-test metrics, or benchmark claims.

## 5. Validation And Review

- [x] 5.1 Run the required MVP CLI, hard-negative mining CLI, Phase 5A dry-run CLI, Phase 5B pilot CLI blocked path, py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check`.
- [x] 5.2 Run a Reviewer subagent over the diff and fix Must Fix items only unless replanning is required.
- [x] 5.3 Commit, push `codex/add-training-pilot-launch-gate`, create a PR, and stop without merge, deploy, archive, model download, real training claim, final-test evaluation, or benchmark-improvement claim.
