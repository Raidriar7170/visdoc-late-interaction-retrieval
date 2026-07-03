## Why

Phase 5E proved that the A100 host has usable GPU capacity and a safe checkout,
but the real pilot remains blocked by two concrete gates: `colpali_engine` is
not importable and no exact A100-readable ColPali / ColQwen `local_model_path`
has been provided. Phase 5F should materialize those runtime gates into
repeatable, public-safe evidence before any real-training pilot is proposed.

## What Changes

- Extend the A100 preflight evidence contract with Phase 5F runtime-gate
  evidence for optional dependency importability, isolated environment/cache
  placement, and model-path readiness.
- Add deterministic local helpers and tests that convert structured A100 gate
  observations into sanitized JSON and Markdown evidence.
- Record whether the runtime is `runtime_ready`, `blocked`, or
  `needs_user_input` without launching training, downloading models, resolving
  remote model IDs, or creating adapters/checkpoints.
- Add Phase 5F report artifacts and a concise Chinese Human Brief that identify
  the remaining blocker and the safe next step.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `a100-real-training-preflight`: Add Phase 5F runtime-gate materialization
  requirements for dependency importability, A100-readable model-path
  validation, sanitized evidence, and no-training side effects.

## Impact

- Updates `visdoc_retrieve.a100_preflight` or a closely scoped helper module.
- Adds focused tests for Phase 5F gate status, blocker codes, path redaction,
  and no-training / no-download / no-checkpoint safety flags.
- Adds sanitized Phase 5F evidence under `reports/training-pilot/`, a progress
  ledger entry, and a short Chinese Human Brief.
- Does not install system packages, download model weights, run real training,
  read final test data, create adapters/checkpoints, or claim benchmark
  improvement.
