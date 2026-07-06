## Why

Phase 5I proved that the A100 runtime can reach the guarded backend layer, but
it still blocks on `backend_training_step_unavailable` because the project has
no reviewed tiny optimizer-backed LoRA runner. Phase 5J should close only that
runner gap while preserving the existing gate, evidence, and no-claim
boundaries.

## What Changes

- Add a repo-owned reviewed backend runner path for the A100 tiny LoRA pilot
  when `backend_dependency=colpali_engine` is importable but does not expose
  the project-specific `run_visdoc_lora_pilot` hook.
- Keep the runner behind the existing `train_lora_pilot` gates:
  `VISDOC_ENABLE_REAL_TRAINING=1`, `allow_real_training=true`,
  `allow_final_test=false`, `local_files_only=true`, CUDA available,
  `max_steps <= 20`, `sample_limit <= 8`, and ignored adapter output.
- Limit the Phase 5J A100 command to a tiny dev-only pilot budget and commit
  only sanitized evidence. If a real optimizer-backed step still cannot run,
  record the exact new blocker instead of faking success.
- Add focused unit tests for the reviewed runner contract, fail-closed behavior,
  and no-final-test/no-benchmark/no-artifact boundaries.
- Do not download models, run final test, add benchmark metrics or improvement
  claims, commit model weights/adapters/caches/private config/private model
  paths, merge, deploy, or archive this change.

## Capabilities

### New Capabilities

- `reviewed-a100-tiny-lora-backend-runner`: Defines the Phase 5J reviewed
  backend runner contract for a bounded A100 tiny LoRA pilot, including
  fail-closed behavior, sanitized evidence, and no-claim/no-artifact
  boundaries.

### Modified Capabilities

None.

## Impact

- Updates `src/visdoc_retrieve/lora_training_backend.py` and focused tests for
  repo-owned reviewed tiny runner behavior.
- Adds Phase 5J OpenSpec artifacts, sanitized `reports/training-pilot/`
  evidence, a concise Chinese Human Brief, and a Phase 5J progress-ledger
  entry.
- Leaves Phase 5I evidence intact as the prior blocked checkpoint and does not
  widen the project into full training, evaluation, benchmark, merge, deploy,
  or archive work.
