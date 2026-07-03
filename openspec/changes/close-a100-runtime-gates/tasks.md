## 1. Contract and tests

- [ ] 1.1 Add failing focused tests for Phase 5G closure evidence: dependency
  gate closed, dependency still blocked, exact model path missing, and
  no-training safety flags.
- [ ] 1.2 Extend the A100 preflight helper with Phase 5G closure evidence while
  preserving Phase 5E and Phase 5F behavior.

## 2. Remote A100 runtime closure attempt

- [ ] 2.1 Re-check A100 storage, checkout, GPU, dependency, cache/temp, and
  exact model-path observations without launching training.
- [ ] 2.2 If safe, create or reuse an isolated allowed-root runtime/cache setup
  and attempt to make `colpali_engine` importable without writing under
  `/root`, `/tmp`, or another user's directory.
- [ ] 2.3 Stop before model download or training if the exact model path remains
  absent, and record the truthful remaining blocker.

## 3. Evidence artifacts

- [ ] 3.1 Generate sanitized Phase 5G JSON, safety, and run-card artifacts under
  `reports/training-pilot/`.
- [ ] 3.2 Update `reports/progress-ledger.yaml` with Phase 5G status, evidence
  paths, remaining blockers, and no-claim boundaries.
- [ ] 3.3 Generate a concise Chinese Human Brief under `docs/human-briefs/`.

## 4. Validation and closeout

- [ ] 4.1 Run focused A100 preflight tests.
- [ ] 4.2 Run full local validation: `pytest -q`, `ruff check .`, `mypy src`,
  `openspec validate --all --strict`, and `git diff --check`.
- [ ] 4.3 Confirm no host IPs, SSH details, process IDs, exact private model
  paths, model weights, adapters, checkpoints, caches, final-test metrics,
  benchmark claims, model downloads, or real-training execution are tracked.
