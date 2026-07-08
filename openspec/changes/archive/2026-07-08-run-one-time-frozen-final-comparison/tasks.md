## 1. Setup and Protocol Review

- [x] 1.1 Create the Phase 6D OpenSpec proposal, design, spec, and task
  artifacts.
- [x] 1.2 Confirm `origin/main` is clean, OpenSpec has no active backlog, and
  GitHub has no open PRs before the Phase 6D branch starts.
- [x] 1.3 Read the frozen Phase 6B protocol and Phase 6C readiness evidence.

## 2. Final Runner and Tests

- [x] 2.1 Add tests for run manifest schema, no-retune pledge, metrics schema,
  support counts, missing-system status, conservative claim checklist, rerun
  guard, and existing CLI behavior.
- [x] 2.2 Add the minimal Phase 6D final-comparison runner and CLI without
  changing retrieval behavior or metric definitions.
- [x] 2.3 Add the checked-in final-comparison config naming the authorized
  command, final split, systems, candidate universe, and output paths.

## 3. One-Time Final Run

- [x] 3.1 Run required pre-final validation commands.
- [x] 3.2 Execute the final comparison once with the frozen command and no
  rerun override.
- [x] 3.3 Write final comparison artifacts, human brief, no-retune pledge, and
  progress-ledger entry.

## 4. Validation and PR

- [x] 4.1 Run post-final JSON, pytest, Ruff, mypy, OpenSpec strict, and diff
  validation.
- [x] 4.2 Confirm no training, tuning after final, model weights, adapters,
  cache artifacts, private config/path, unsupported improvement claim, README
  overclaim, or fabricated missing-system metrics are tracked.
- [x] 4.3 Commit, push `codex/run-one-time-frozen-final-comparison`, create a
  PR, and stop without merge, deploy, training, tuning, or rerunning the final
  comparison.
