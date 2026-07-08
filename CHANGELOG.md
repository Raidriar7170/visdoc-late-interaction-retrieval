# Changelog

## v0.1.0 - 2026-07-08

### Added

- Page-level VisDoc-Retrieve project scaffold with synthetic smoke corpus,
  split-aware page/query manifests, and candidate-universe metadata.
- Deterministic BM25, lexical cosine, RRF, mock visual MaxSim scaffold, and
  diagnostic MVP retrieval surfaces.
- Hard-negative mining over train/dev only.
- Training readiness, pilot launch, A100 runtime/model-path gates, tiny A100
  runner proof, and dev-only pilot evaluation harness.
- Frozen final-comparison protocol, execution dry-run gate, one-time Phase 6D
  final comparison, final metrics, final rankings, claim checklist, and
  no-retune pledge.
- Final presentation package with project card, resume bullets, interview
  talking points, evidence index, and Human Briefs.

### Final Result Boundary

- Phase 6D completed a one-time frozen final comparison and read the final test
  once under `phase-6b-final-comparison-protocol/v1`.
- The final claim checklist records `no_clear_improvement_claim`; this release
  does not claim benchmark improvement or model superiority.
- `mock_visual` is a deterministic scaffold, not real visual-model performance.
- `tiny_lora_adapter` and `zero_shot_visual_backend` are `not_available`; their
  metrics were not fabricated.
- No model weights, adapter checkpoints, training caches, private configs, or
  exact private model paths are committed.

### Not Included

- No production deployment.
- No real visual model benchmark row.
- No trained adapter benchmark row.
- No benchmark improvement claim.
- No retuning or rerun after final-test access.
