## 1. Planning

- [x] 1.1 Create OpenSpec proposal, design, spec, and task artifacts for
  `freeze-final-comparison-protocol`.
- [x] 1.2 Confirm the phase starts from clean `origin/main` in an isolated
  branch/worktree.

## 2. Protocol Evidence

- [x] 2.1 Add a final-comparison protocol document that freezes final-test
  access gates, allowed labels, comparison schema, and public-claim rules.
- [x] 2.2 Add machine-readable protocol evidence for status, schema, and claim
  checklist boundaries.
- [x] 2.3 Add a concise Chinese Human Brief for Phase 6B.
- [x] 2.4 Add a Phase 6B entry to `reports/progress-ledger.yaml`.

## 3. Hygiene and Validation

- [x] 3.1 Confirm no model weights, adapter checkpoints, training caches,
  private local config, exact private model path, final-test metrics,
  benchmark-improvement claim, README result claim, `.worktrees`, or
  `.codex/skills/openspec-sync-specs` are tracked.
- [x] 3.2 Run required CLI, compile, parse, pytest, Ruff, mypy, OpenSpec, and
  diff-check validation.
- [x] 3.3 Commit, push, create PR, and stop without merge, deploy, training,
  final-test execution, or OpenSpec archive.
