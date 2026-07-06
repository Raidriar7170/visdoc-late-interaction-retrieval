## 1. OpenSpec and Branch Setup

- [x] 1.1 Create the Phase 5K OpenSpec proposal, design, spec, and task artifacts.
- [x] 1.2 Confirm the work starts from clean `origin/main` in a dedicated
  branch/worktree.

## 2. Dev-Only Harness Implementation

- [x] 2.1 Add focused tests for final-test exclusion, dev-only eval schema,
  missing-adapter `not_available`, comparison schema no-fabrication, tiny
  budget gates, private path redaction, and forbidden artifact tracking.
- [x] 2.2 Add an import-safe Phase 5K harness and CLI that reads sanitized pilot
  manifests and dev split artifacts only.
- [x] 2.3 Generate Phase 5K evidence files and update the progress ledger.
- [x] 2.4 Add a concise Chinese Human Brief that preserves all no-claim
  boundaries.

## 3. Validation and PR Closeout

- [x] 3.1 Run the required CLI, compile, parse, pytest, Ruff, mypy, OpenSpec,
  and diff-check validation commands.
- [x] 3.2 Confirm no model weights, adapter checkpoints, caches, `.worktrees`,
  `.codex/skills/openspec-sync-specs`, private local model path, private local
  config, final-test metrics, README result claims, or benchmark-improvement
  claims are tracked.
- [x] 3.3 Commit, push `codex/phase-5k-dev-only-pilot-evaluation-harness`,
  create a PR, and stop without merge, deploy, or OpenSpec archive.
