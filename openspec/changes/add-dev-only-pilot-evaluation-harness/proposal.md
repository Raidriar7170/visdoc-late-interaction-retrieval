## Why

Phase 5J proved the reviewed tiny LoRA runner path, and Phase 5I/5J are now
archived. The project still needs a reproducible Phase 5K dev-only evaluation
harness that can inspect sanitized pilot evidence and dev split sanity without
turning tiny pilot output into a final benchmark or improvement claim.

## What Changes

- Add a Phase 5K dev-only pilot evaluation harness that reads sanitized pilot
  manifests, dev-only split artifacts, and optional baseline summaries.
- Emit public-safe Phase 5K evidence under `reports/training-pilot/` and a
  concise Human Brief.
- Record adapter availability as `not_available` when no committed adapter
  exists instead of fabricating metrics.
- Record comparison schema entries for text baseline, optional zero-shot visual
  baseline, and tiny pilot adapter status without claiming benchmark
  improvement.
- Keep tiny pilot execution out of this local harness path unless every
  existing real-training gate passes; if the A100/runtime path is unavailable,
  emit skipped/blocked evidence only.
- Do not download models, use network access, run final test, claim benchmark
  improvement, commit model weights, commit adapter checkpoints, commit caches,
  commit private local config, commit exact private model paths, merge, deploy,
  or archive this change.

## Capabilities

### New Capabilities

- `dev-only-pilot-evaluation-harness`: Defines the Phase 5K dev-only pilot
  evaluation harness, public-safe evidence schema, no-final-test/no-benchmark
  boundaries, and missing-adapter behavior.

### Modified Capabilities

None.

## Impact

- Adds a small import-safe Phase 5K harness module and CLI entrypoint under
  `src/visdoc_retrieve/`.
- Adds focused tests for dev-only reads, final-test exclusion, missing adapter
  status, private path redaction, comparison schema boundaries, and existing
  CLI preservation.
- Adds Phase 5K OpenSpec artifacts, sanitized evidence files, a Human Brief,
  and a progress-ledger entry.
