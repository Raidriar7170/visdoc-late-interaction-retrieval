# Run One-Time Frozen Final Comparison

## Summary

Execute the Phase 6D one-time frozen final comparison under the archived Phase
6B protocol and archived Phase 6C execution gate. This change authorizes one
final-test read, records immutable run provenance, writes final benchmark
evidence, and keeps all unsupported systems and claims explicitly blocked or
not available.

## Motivation

Phase 6B froze the final-comparison protocol and Phase 6C verified readiness
without reading final-test data. The repository now needs the one authorized
final benchmark run so the project can publish final metrics without changing
retrieval behavior, metric definitions, candidate universe, or test labels
after seeing results.

## Scope

- Add a minimal Phase 6D final-comparison runner and CLI that reuse existing
  deterministic retrievers and metric computation.
- Add a checked-in final-comparison config naming the authorized final split,
  candidate universe, systems, and output paths.
- Execute the final comparison once on the frozen `test` split in the checked-in
  synthetic smoke manifests.
- Write the run manifest, final metrics, rankings, report, claim checklist,
  no-retune pledge, human brief, and progress-ledger entry.
- Add tests covering manifest/schema, metrics, support counts, missing-system
  handling, claim blocking, and rerun guard behavior.

## Out of Scope

- Training, tuning, model download, A100/SSH/GPU use, deployment, or changing
  retrieval behavior.
- Changing final-test labels/qrels, metric definitions, candidate universe, or
  frozen protocol semantics.
- Committing model weights, adapter checkpoints, cache artifacts, private
  config, or exact private local model paths.
- Turning dev-only or tiny-runner evidence into model-performance claims.

## Safety Boundaries

The runner MUST fail closed if default final outputs already exist unless an
explicit test-only override is used. The committed Phase 6D run MUST use the
normal no-override command exactly once. Final report wording MUST state whether
the outcome supports an improvement claim; mixed or weak results must be
reported directly.
