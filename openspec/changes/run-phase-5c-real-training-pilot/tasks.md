## 1. OpenSpec And Worktree Setup

- [x] 1.1 Create the Phase 5C OpenSpec proposal, design, spec, and task artifacts.
- [x] 1.2 Validate the Phase 5C OpenSpec change with strict validation before evidence generation.
- [x] 1.3 Confirm the implementation is running in a clean dedicated branch/worktree from `origin/main`.

## 2. Pilot Preconditions

- [x] 2.1 Inspect the A100 environment for GPU/CUDA availability without interrupting other users' processes.
- [x] 2.2 Resolve whether the exact private remote repository path and local model path are available; if unavailable, keep the outcome blocked.
- [x] 2.3 Prepare a local-only ignored Phase 5C pilot config with `allow_real_training=true`, `allow_final_test=false`, `max_steps <= 20`, ignored adapter output, and no committed private path.

## 3. Pilot Or Blocked Evidence

- [x] 3.1 Run `VISDOC_ENABLE_REAL_TRAINING=1 PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot --config <local_config>` or record why it cannot be run from the target environment.
- [x] 3.2 Generate sanitized Phase 5C environment-check, safety-check, run-card, adapter-manifest, and dev-eval evidence for the actual pilot or blocked outcome.
- [x] 3.3 Generate a concise Chinese human brief and Phase 5C progress-ledger entry.
- [x] 3.4 Confirm no model weights, adapter checkpoints, caches, `.worktrees`, local configs with private paths, final-test metrics, benchmark claims, or README result claims are staged.

## 4. Validation And Review

- [x] 4.1 Run the required MVP, hard-negative mining, Phase 5A dry-run, Phase 5B blocked pilot, py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check` commands.
- [x] 4.2 Run a Reviewer subagent over the diff and fix Must Fix items only unless replanning is required.
- [x] 4.3 Commit, push `codex/phase-5c-real-training-pilot`, create a PR, and stop without merge, deploy, or OpenSpec archive.
