## 1. Runtime gate contract and tests

- [x] 1.1 Add failing focused tests for Phase 5F dependency gate, model-path
  gate, `runtime_ready` status, redaction, and no-training safety flags.
- [x] 1.2 Extend the A100 preflight helper with Phase 5F runtime-gate evidence
  while preserving Phase 5E behavior.

## 2. Phase 5F evidence artifacts

- [x] 2.1 Generate sanitized Phase 5F environment, safety, and run-card
  evidence under `reports/training-pilot/`.
- [x] 2.2 Update `reports/progress-ledger.yaml` with Phase 5F status, blockers,
  evidence paths, and no-claim boundaries.
- [x] 2.3 Generate a concise Chinese Human Brief under `docs/human-briefs/`.

## 3. Validation and closeout

- [x] 3.1 Run focused Phase 5F tests and keep existing Phase 5E tests passing.
- [x] 3.2 Run local validation: `pytest -q`, `ruff check .`, `mypy src`,
  `openspec validate --all --strict`, and `git diff --check`.
- [x] 3.3 Confirm no host IPs, SSH details, process IDs, exact private model
  paths, model weights, adapters, checkpoints, caches, final-test metrics,
  benchmark claims, model downloads, or real-training execution are tracked.
