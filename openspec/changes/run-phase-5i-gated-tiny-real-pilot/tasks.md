## 1. OpenSpec and Practical Loop Setup

- [x] 1.1 Create the Phase 5I OpenSpec proposal, design, spec, and task artifacts.
- [x] 1.2 Refresh the tracked `opsx-auto practical` goal/phase inputs so the
  new Phase 5I change path and YAML manifest convention are admitted.
- [x] 1.3 Confirm the implementation is running in a clean dedicated branch/worktree
  from `origin/main`.

## 2. Launcher and Boundary Updates

- [x] 2.1 Add focused tests for Phase 5I public metadata overrides while preserving
  Phase 5D defaults.
- [x] 2.2 Parameterize the pilot public evidence layer, ignore `local/`, and keep
  the guarded training logic and safety caps unchanged.

## 3. A100 Gated Pilot Attempt

- [x] 3.1 Refresh the A100 checkout/worktree, inspect CUDA/GPU occupancy safely,
  and prepare an untracked `local/train_lora_pilot.phase5i.local.json` config
  with the exact local model path, tiny budget, and ignored adapter output.
- [x] 3.2 Run the guarded Phase 5I pilot command with
  `VISDOC_ENABLE_REAL_TRAINING=1`, then keep the truthful outcome as either a
  pilot run or blocked checkpoint.
- [x] 3.3 Commit only sanitized Phase 5I evidence: environment check, safety
  check, run-card, adapter manifest, dev-eval JSON, Human Brief, and
  progress-ledger entry.

## 4. Validation and PR Closeout

- [x] 4.1 Run the required focused and full validation commands, including the
  existing blocked example pilot command and `git diff --check`.
- [x] 4.2 Confirm no model weights, adapter checkpoints, caches, `.worktrees`,
  private local model path, private local config, final-test metrics, README
  result claims, or benchmark-improvement claims are tracked.
- [ ] 4.3 Commit, push `codex/phase-5i-gated-tiny-real-pilot`, create a PR, and
  stop without merge, deploy, or OpenSpec archive.
