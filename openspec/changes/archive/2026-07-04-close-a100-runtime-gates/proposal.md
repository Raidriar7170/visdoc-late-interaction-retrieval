## Why

Phase 5F materialized repeatable A100 runtime gates, and the current A100
probe still shows two concrete blockers: `colpali_engine` is not importable in
the checked runtime and the exact model directory
`/mnt/data/minghongsun/models/vidore-colqwen2-v1.0-hf` is absent. The next
step should close every gate that can be safely closed under
`/mnt/data/minghongsun` and commit truthful public-safe closure evidence before
any real-training pilot is proposed.

## What Changes

- Add Phase 5G runtime-gate closure evidence for a checked A100 runtime after
  an isolated allowed-root dependency setup attempt.
- Permit creating or reusing an isolated Python runtime and cache/temp
  directories under `/mnt/data/minghongsun`; do not write project files, caches,
  or temporary outputs under `/root`, `/tmp`, or another user's directory.
- Record whether `colpali_engine` importability was closed, still blocked, or
  blocked by dependency installation limits.
- Verify the exact A100-side model path only; if the directory is still absent,
  record `missing_local_model_path` or `needs_user_model_path` instead of
  downloading weights or inferring readiness from unrelated model directories.
- Generate sanitized Phase 5G JSON, safety, run-card, progress-ledger, and
  concise Chinese Human Brief evidence with no training execution or benchmark
  claims.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `a100-real-training-preflight`: Add Phase 5G runtime-gate closure
  requirements for allowed-root dependency setup attempts, exact model-path
  verification, truthful ready/blocked outcomes, and no-training safety
  evidence.

## Impact

- May update `visdoc_retrieve.a100_preflight` or a closely scoped helper module
  to distinguish Phase 5G closure evidence from Phase 5F materialization.
- Adds focused tests for dependency-closed, model-path-missing, and no-training
  closure evidence.
- May create an isolated runtime/cache on the A100 host under
  `/mnt/data/minghongsun`, but committed evidence must be redacted and
  public-safe.
- Does not download model weights, launch real training, create adapters or
  checkpoints, read final test data, or claim retrieval improvement.
