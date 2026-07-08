## Why

Phase 6B froze the final-comparison protocol and the OpenSpec backlog is now
clean, but the repository still needs an executable preflight gate that can
verify readiness without reading final-test files or running the final
comparison. Adding a dry-run gate now makes the next authorized final run
auditable while preserving the no-benchmark-claim boundary.

## What Changes

- Add a Phase 6C final-comparison execution gate / dry-run capability.
- Add a local-only report generator that reads the frozen Phase 6B protocol
  evidence, checks required artifacts, checks active OpenSpec state, locks the
  final-test guard, and emits planned-run/readiness evidence.
- Add machine-readable Phase 6C evidence, a Markdown readiness report, a
  claim checklist, a concise Human Brief, and a progress-ledger entry.
- Add tests for final-test non-access, OpenSpec active-state handling,
  missing-artifact status, claim blocking, report schema, output-path safety,
  and existing CLI behavior.
- Do not train, use A100/GPU/SSH, download models, run final test, run the
  real final comparison, tune, deploy, or add benchmark improvement claims.

## Capabilities

### New Capabilities

- `final-comparison-execution-gate`: Defines the Phase 6C dry-run gate that
  validates frozen-protocol readiness and produces non-final execution
  readiness evidence without final-test access or benchmark claims.

### Modified Capabilities

- None.

## Impact

- Affected code: a new import-safe final-comparison dry-run module and CLI
  under `src/visdoc_retrieve/`.
- Affected artifacts: Phase 6C reports under
  `reports/final-comparison-protocol/`, a Human Brief, progress ledger, tests,
  and OpenSpec change files.
- No source behavior changes for MVP, hard-negative mining, training dry-run,
  or pilot launch gate beyond regression coverage.
- No model weights, adapter checkpoints, training caches, private config,
  exact private model paths, final-test metrics, final-comparison results,
  README result claims, or benchmark improvement claims are introduced.
