## 1. Preflight tooling and contract

- [x] 1.1 Add a minimal Phase 5E preflight evidence writer or script that keeps
  committed output public-safe and deterministic.
- [x] 1.2 Add focused tests for sanitization, blocker codes, and no-training /
  no-model-download / no-final-test flags.

## 2. Remote A100 setup/preflight

- [x] 2.1 Verify or prepare the remote checkout only under
  `/mnt/data/minghongsun/visdoc-late-interaction-retrieval`.
- [x] 2.2 Check CUDA/GPU visibility, idle GPU candidates, Python runtime, and
  optional dependency importability without launching training.
- [x] 2.3 Check whether an exact local ColPali / ColQwen model path is available;
  if unavailable, record `needs_user_model_path` without guessing.

## 3. Evidence and documentation

- [x] 3.1 Commit sanitized Phase 5E environment/safety/readiness evidence under
  `reports/training-pilot/`.
- [x] 3.2 Update `reports/progress-ledger.yaml` with the Phase 5E status and
  no-claim boundaries.
- [x] 3.3 Generate a concise Chinese Human Brief under `docs/human-briefs/`.
- [x] 3.4 Confirm no host IPs, SSH details, process IDs, exact private model
  paths, model weights, adapters, checkpoints, caches, final-test metrics, or
  benchmark claims are tracked.

## 4. Validation and closeout

- [x] 4.1 Run focused tests for the new Phase 5E preflight path.
- [x] 4.2 Run the local validation baseline: MVP, hard negatives, dry run,
  expected blocked pilot, py_compile, pyproject parse, pytest, Ruff, mypy,
  OpenSpec strict validation, and `git diff --check`.
- [x] 4.3 Summarize the remote readiness result and remaining blocker without
  archiving, deploying, merging, or starting real training.
