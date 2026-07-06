## 1. OpenSpec and Branch Setup

- [x] 1.1 Create Phase 5J proposal, design, spec, and task artifacts.
- [x] 1.2 Confirm the work is isolated in a dedicated branch/worktree stacked
  on the Phase 5I evidence branch.
- [x] 1.3 Confirm the baseline focused launcher tests pass before runner edits.

## 2. Reviewed Runner Implementation

- [x] 2.1 Add focused tests for repo-owned runner selection when
  `colpali_engine` is importable but lacks `run_visdoc_lora_pilot`.
- [x] 2.2 Add focused tests for successful tiny optimizer-backed runner output
  using fake model, processor, tensor, optimizer, and PEFT modules.
- [x] 2.3 Add focused tests for fail-closed blocked results when model loading,
  processor encoding, LoRA wrapping, optimizer step, or adapter save fails.
- [x] 2.4 Implement the lazy-imported repo-owned ColQwen2 tiny runner while
  preserving third-party hook precedence and all existing safety checks.

## 3. Phase 5J A100 Attempt and Evidence

- [x] 3.1 Refresh the A100 worktree safely under `/mnt/data/minghongsun`, inspect
  GPU occupancy, and prepare an ignored Phase 5J local pilot config.
- [x] 3.2 Run the guarded Phase 5J tiny command with
  `VISDOC_ENABLE_REAL_TRAINING=1` and an explicitly selected idle GPU.
- [x] 3.3 Commit only sanitized Phase 5J evidence: environment check, safety
  check, run-card, adapter manifest, dev-eval JSON, Human Brief, and
  progress-ledger entry.

## 4. Validation and PR Closeout

- [x] 4.1 Run focused tests, existing launcher tests, OpenSpec strict
  validation, Ruff, and `git diff --check`.
- [x] 4.2 Confirm no model weights, adapter checkpoints, caches, `.worktrees`,
  private local model path, private local config, final-test metrics, README
  result claims, or benchmark-improvement claims are tracked.
- [x] 4.3 Commit, push `codex/phase-5j-reviewed-a100-tiny-lora-runner`, create
  or update a PR, and stop without merge, deploy, or OpenSpec archive.
