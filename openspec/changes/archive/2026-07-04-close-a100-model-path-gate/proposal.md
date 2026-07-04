## Why

Phase 5G closed the A100 dependency/runtime gates but left the real pilot
blocked by the exact A100-side model path. The model directory is now present
on the A100 host, so this phase should close only the model-path gate with
public-safe evidence before any real-training launch is considered.

## What Changes

- Add Phase 5H model-path gate closure evidence for the exact A100-side model
  directory using static filesystem markers only.
- Record redacted model-path readiness, marker readiness, and inherited
  runtime-gate status without committing the exact private path.
- Generate sanitized Phase 5H JSON, safety, run-card, progress-ledger, and
  concise Chinese Human Brief evidence.
- Preserve the hard boundary that this phase does not launch training, load the
  model, call `from_pretrained`, download weights, create adapters or
  checkpoints, use final test data, or claim benchmark improvement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `a100-real-training-preflight`: Add Phase 5H exact model-path marker closure
  requirements, public-safe redaction, and no-training runtime-ready evidence.

## Impact

- Updates `visdoc_retrieve.a100_preflight` with a Phase 5H evidence writer and
  run-card renderer.
- Adds focused tests for marker-ready, missing, malformed, outside-root, CLI,
  and no-training safety outcomes.
- Adds Phase 5H evidence artifacts under `reports/training-pilot/`, a progress
  ledger entry, and a Human Brief.
- Does not add runtime dependencies, download model files, start training,
  create model artifacts, or change retrieval/training behavior.
