## Why

Phase 5K and Phase 6A established a public evidence surface, but the repository
still needs a frozen contract that explains when final-test evaluation may run
and what evidence is required before any benchmark or improvement claim is
allowed. Freezing that protocol now prevents dev-only, tiny-runner, and future
longer-dev evidence from being misread as final benchmark results.

## What Changes

- Add a final-comparison protocol capability that defines final-test access
  gates, comparison-table schema requirements, and claim-review requirements.
- Add documentation evidence for Phase 6B that freezes the allowed labels for
  dev-only sanity, tiny runner proof, longer dev training, and final benchmark.
- Add a public-safe claim checklist for reviewer and recruiter-facing surfaces.
- Add a Phase 6B progress-ledger entry.
- Do not train, use A100/GPU/SSH, download models, run final test, deploy, or
  add benchmark improvement claims.

## Capabilities

### New Capabilities

- `final-comparison-protocol`: Defines the frozen final-comparison protocol,
  including final-test access gates, comparison schema, claim checklist, and
  evidence boundaries.

### Modified Capabilities

- None.

## Impact

- Affected files are OpenSpec artifacts, docs, reports, and the progress ledger.
- No source behavior, configs, dependencies, model artifacts, adapter
  checkpoints, cache artifacts, private paths, final-test metrics, or benchmark
  claims are introduced.
