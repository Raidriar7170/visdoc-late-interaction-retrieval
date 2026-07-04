## 1. Contract and tests

- [x] 1.1 Add focused failing tests for Phase 5H marker-ready, missing,
  incomplete-marker, outside-root, CLI, redaction, and no-training safety
  outcomes.
- [x] 1.2 Extend the A100 preflight helper with Phase 5H model-path gate
  closure evidence while preserving Phase 5E/5F/5G behavior.

## 2. A100 model-path observation

- [x] 2.1 Refresh the A100 checkout and marker observation without launching
  training, loading the model, downloading weights, or creating adapters.
- [x] 2.2 Record only static marker readiness for the exact A100-side model
  path and keep all runtime/cache/temp/log paths under the allowed root.

## 3. Evidence artifacts

- [x] 3.1 Generate sanitized Phase 5H JSON, safety, and run-card artifacts under
  `reports/training-pilot/`.
- [x] 3.2 Update `reports/progress-ledger.yaml` with Phase 5H status, evidence
  paths, closed gates, and no-claim boundaries.
- [x] 3.3 Generate a concise Chinese Human Brief under `docs/human-briefs/`.

## 4. Validation and closeout

- [x] 4.1 Run focused A100 preflight tests.
- [x] 4.2 Run full local validation: `pytest -q`,
  `pytest -q tests/test_a100_preflight.py`, `ruff check .`, `mypy src`,
  `openspec validate close-a100-model-path-gate --strict`,
  `openspec validate --all --strict`, and `git diff --check`.
- [x] 4.3 Confirm no host IPs, SSH details, process IDs, exact private model
  paths in Phase 5H reports/Human Brief, model weights, adapters,
  checkpoints, caches, final-test metrics, benchmark claims, model downloads,
  model loading, or real-training execution are tracked.
