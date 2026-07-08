## Context

The repository now contains a frozen Phase 6B final-comparison protocol,
machine-readable protocol status, comparison schema, and claim checklist. PR
#23 archived the old completed OpenSpec backlog, so Phase 6C can check whether
the final-comparison execution gate is ready without carrying stale active
changes.

Phase 6C is intentionally not the final benchmark. It is a local dry-run gate:
it verifies protocol and evidence inputs, proves final-test access remains
locked, and writes planned-run/readiness artifacts for a later Phase 6D
one-time final comparison.

## Goals / Non-Goals

**Goals:**

- Read the frozen Phase 6B protocol and evidence artifacts.
- Verify the current OpenSpec active-change state and record whether only the
  Phase 6C change is active during development.
- Verify required protocol, schema, claim, candidate-universe, split-policy,
  metric-definition, MVP, hard-negative, training, and dev-only harness
  artifacts.
- Emit a dry-run report, readiness report, claim checklist, Human Brief, and
  progress-ledger entry.
- Keep missing optional artifacts honest as `missing` or `blocked`.

**Non-Goals:**

- No training, tuning, A100/GPU/SSH, model downloads, final-test reads, real
  final comparison, deployment, benchmark improvement claims, README result
  claims, model weights, adapter checkpoints, caches, private config, or exact
  private model paths.

## Decisions

- Implement a small import-safe Python module instead of a shell script. This
  gives tests direct access to path validation, OpenSpec state parsing, and
  report schema generation.
- Treat final-test paths as forbidden inputs and as planned future paths only.
  The module records path strings but never opens final-test qrels, labels, or
  metrics files.
- Use `openspec list --json` when available and fall back to plain
  `openspec list` parsing for local compatibility. In tests, active changes
  are injected directly so no subprocess is required.
- Mark the gate `ready_for_phase_6d` only when all required artifacts exist,
  the final-test guard is locked, benchmark claims are blocked, output paths
  are safe, and active OpenSpec state is either exactly the current Phase 6C
  change or empty in a post-merge context.
- Keep comparison execution state as `dry_run_only` / `not_executed`; planned
  run rows contain expected artifact paths and statuses, not metrics.

## Risks / Trade-offs

- The gate can be ready while final comparison is still not authorized -> The
  readiness report labels the next step as Phase 6D and keeps
  `final_comparison_execution=not_executed`.
- Local OpenSpec CLI output can differ by version -> The implementation accepts
  injected active changes for tests and has a plain-text fallback.
- Evidence paths can drift -> Tests cover missing artifacts and the report
  marks them `missing`/`blocked` instead of fabricating readiness.
- Output generation can accidentally target unsafe directories -> Path
  validation rejects `.local`, caches, checkpoints, worktrees, private configs,
  and final-test output roots.

## Migration Plan

- Add the Phase 6C OpenSpec artifacts.
- Add the dry-run module and CLI.
- Generate Phase 6C evidence from the checked-in frozen protocol artifacts.
- Update the progress ledger and add a Human Brief.
- Run local validation and open a PR without merge, deploy, archive, training,
  final-test execution, or final comparison.
