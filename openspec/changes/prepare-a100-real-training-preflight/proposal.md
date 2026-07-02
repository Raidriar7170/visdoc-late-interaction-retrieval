## Why

Phase 5D merged guarded real-training backend wiring, but the A100 environment
still lacks confirmed repo checkout, required optional runtime package(s), and
an exact local ColPali / ColQwen model path. Phase 5E should make the remote
environment truth surface explicit before any tiny real pilot is attempted.

## What Changes

- Add a Phase 5E A100 preflight that checks only remote setup prerequisites:
  allowed storage root, repo checkout under `/mnt/data/minghongsun`, Python
  runtime, optional training dependencies, CUDA/GPU availability, safe idle-GPU
  candidate selection, local model path presence, and cache/env locations.
- Prepare or verify a remote checkout under the allowed A100 storage root
  without writing project files, caches, checkpoints, logs, or temporary outputs
  under `/root`, `/tmp`, or other users' directories.
- Emit sanitized Phase 5E evidence that records whether each prerequisite is
  ready or blocked, while redacting private paths and excluding host IPs, SSH
  details, process IDs, secrets, model weights, adapters, and checkpoints.
- Add a concise Chinese Human Brief and progress-ledger entry that truthfully
  says whether the real pilot remains blocked or is preflight-ready.
- Do not start training, download models, install system packages, run final
  test data, create adapters/checkpoints, claim benchmark improvement, archive
  OpenSpec, merge, or deploy.

## Capabilities

### New Capabilities

- `a100-real-training-preflight`: Defines Phase 5E remote A100 setup and
  prerequisite preflight evidence before any real-training pilot is launched.

### Modified Capabilities

None.

## Impact

- Adds OpenSpec artifacts for the Phase 5E preflight checkpoint.
- May add a local-only preflight script or helper under `scripts/` that executes
  read-only checks and writes only sanitized evidence into repo report paths.
- Adds Phase 5E evidence under `reports/training-pilot/`, a concise Chinese
  human brief under `docs/human-briefs/`, and a progress-ledger entry.
- Uses the remote A100 host through an existing SSH alias, but committed
  evidence must not include private network addresses, SSH config, secrets,
  process IDs, or exact private model paths.
- Preserves Phase 5D backend behavior and keeps real training, model downloads,
  adapter creation, and final-test evaluation out of scope.
