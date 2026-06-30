## 1. OpenSpec And RED Tests

- [x] 1.1 Create and validate proposal, design, spec deltas, and task list.
- [x] 1.2 Add RED tests for visual zero-shot config parsing, missing local
  model path errors, check-config behavior, and import-safe real adapter.
- [x] 1.3 Add RED tests for deterministic mock behavior, MaxSim coverage, real
  token-cache schema round-trip, cache shape validation, and unchanged MVP
  execution.

## 2. Backend And CLI Implementation

- [x] 2.1 Add visual zero-shot config dataclasses, loader, path validation, and
  local-only backend policy.
- [x] 2.2 Add an import-safe local visual model backend adapter scaffold with
  clear missing-path and missing-runtime errors.
- [x] 2.3 Add generic visual token embedding cache schema helpers compatible
  with MaxSim.
- [x] 2.4 Add optional `run_visual_zero_shot` CLI with `--check-config` and
  `--dry-run`, while preserving `run_mvp` behavior unchanged.

## 3. Configs And Evidence Docs

- [x] 3.1 Add `configs/visual_zero_shot.local.example.json` and config docs.
- [x] 3.2 Add the Chinese human brief for the visual zero-shot backend
  checkpoint.
- [x] 3.3 Update `reports/progress-ledger.yaml` with started/scaffolded and
  not-started boundaries.

## 4. Validation, Review, And Closeout

- [x] 4.1 Run the required MVP smoke, compile, pyproject parse, pytest, Ruff,
  mypy, OpenSpec strict, and diff whitespace validation commands.
- [x] 4.2 Run extra checks for import safety, no committed model weights/cache
  artifacts, no committed `.worktrees`, and no README benchmark claim.
- [x] 4.3 Run Reviewer, fix Must Fix items only, rerun affected validation, then
  commit, push, and create a PR without merging.
