## 1. OpenSpec and Branch Setup

- [x] 1.1 Create the Phase 6C OpenSpec proposal, design, spec, and task
  artifacts.
- [x] 1.2 Confirm the work starts from clean `origin/main` in a dedicated
  branch/worktree.

## 2. Dry-Run Gate Implementation

- [x] 2.1 Add focused tests for final-test non-access, active OpenSpec state,
  missing artifact status, claim blocking, report schema, output-path safety,
  and existing CLI behavior.
- [x] 2.2 Add an import-safe Phase 6C dry-run gate module and CLI.
- [x] 2.3 Generate Phase 6C evidence files and update the progress ledger.
- [x] 2.4 Add a concise Chinese Human Brief that states Phase 6C is dry-run
  gate only and Phase 6D is the later one-time final comparison.

## 3. Validation and PR Closeout

- [x] 3.1 Run the required CLI, compile, parse, pytest, Ruff, mypy, OpenSpec,
  and diff-check validation commands.
- [x] 3.2 Confirm no model weights, adapter checkpoints, caches, `.worktrees`,
  `.codex/skills/openspec-sync-specs`, private local model path, private local
  config, final-test metrics, final-comparison results, README result claims,
  or benchmark-improvement claims are tracked.
- [x] 3.3 Commit, push `codex/add-final-comparison-execution-gate-dry-run`,
  create a PR, and stop without merge, deploy, final-test execution, final
  comparison, training, or OpenSpec archive.
