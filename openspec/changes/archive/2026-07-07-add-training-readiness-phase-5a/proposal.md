## Why

The project now has deterministic MVP retrieval, an optional local visual
zero-shot backend scaffold, and hard-negative mining artifacts, but it still
lacks a frozen, validated package that says exactly what would be safe to hand
to a future LoRA / QLoRA training run. This change adds a training-readiness
checkpoint so Phase 5B can begin from explicit artifacts, split boundaries, and
safety statements instead of ad hoc local assumptions.

## What Changes

- Add local-only training-readiness configs for dry-run validation and future
  local model path checking.
- Add a hard-negative triple dataset loader that validates schema, split
  boundaries, candidate-universe identity, positive/negative separation, and
  deterministic ordering.
- Add a CPU-safe mock ranking scorer/loss smoke surface that requires no torch,
  GPU, model download, or external service by default.
- Add a dry-run trainer entry point that parses config, freezes artifact
  hashes, loads triples, runs leakage checks, constructs mock batches, computes
  mock loss, and writes readiness reports.
- Add training-readiness artifacts, a concise human brief, progress-ledger
  entry, and tests covering safety boundaries and existing CLI preservation.
- Do not run training, download weights, create adapter checkpoints, evaluate
  final test data, or add benchmark/improvement claims.

## Capabilities

### New Capabilities
- `training-readiness`: Defines the local-only Phase 5A readiness contract for
  artifact freeze, hard-negative triples, dry-run loss/trainer behavior,
  safety checks, and no-training/no-claim boundaries.

### Modified Capabilities

None.

## Impact

- Adds configs under `configs/` for dry-run readiness and local-only future
  model path checking.
- Adds Python modules under `src/visdoc_retrieve/` for config parsing,
  dataset loading, mock ranking loss, artifact freeze, and dry-run report
  generation.
- Adds tests for the new readiness surface and regression coverage for MVP,
  hard-negative mining, and optional visual backend import safety.
- Adds deterministic report artifacts under `reports/training-readiness/`,
  updates `reports/progress-ledger.yaml`, and adds a human review brief under
  `docs/human-briefs/`.
