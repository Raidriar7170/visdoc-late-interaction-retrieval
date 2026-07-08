# Design

## Inputs

Phase 6D reads these frozen inputs:

- Protocol: `docs/final-comparison-protocol.md`
- Protocol/spec requirements:
  `openspec/specs/final-comparison-protocol/spec.md` and
  `openspec/specs/final-comparison-execution-gate/spec.md`
- Readiness evidence:
  `reports/final-comparison-protocol/phase-6c-execution-gate-dry-run.json`
- Metrics definition: `openspec/specs/retrieval-evaluation-metrics/spec.md`
- Pages manifest: `data/synthetic-smoke/pages.jsonl`
- Query/qrels manifest: `data/synthetic-smoke/queries.jsonl`
- Authorized final split: `test`

The repository has no separate `data/final-test/qrels.jsonl`; the final qrels
are the `test` split rows in the checked-in query manifest. The run manifest
therefore records both full-file hashes and filtered final-split hashes.

## Runner Shape

Add `visdoc_retrieve.final_comparison_run` plus
`visdoc_retrieve.run_final_comparison`:

- Load a small config from `configs/final_comparison.json`.
- Validate that OpenSpec active state contains only the Phase 6D change.
- Validate that Phase 6C readiness is `ready_for_phase_6d`.
- Resolve candidate pages and queries using the frozen candidate universe.
- Run only already-implemented deterministic systems:
  `bm25`, `lexical_cosine`, `bm25_lexical_rrf`, and `mock_visual`.
- Record optional systems as `not_available` when no frozen artifact exists:
  zero-shot visual backend and tiny LoRA adapter.
- Compute Recall@1, Recall@5, MRR, NDCG@10, subset metrics, and support counts
  using `compute_retrieval_metrics`.
- Write final evidence artifacts under `reports/final-comparison/`.

## Once Guard

The default run fails if any committed final output already exists. Tests may
use temporary output paths and an explicit `allow_rerun` flag to prove rerun
guard behavior, but the committed Phase 6D command must not use the override.

## Claim Checklist

The claim checklist only allows an improvement claim if:

- final test was read by the authorized Phase 6D command;
- final comparison metrics were generated;
- all artifact hygiene checks pass;
- baseline rows exist with matching split scope;
- a reviewer approval field is recorded.

If the measured results are mixed, tied, or unsupported, the final report keeps
the claim status as `no_clear_improvement_claim`.

## Risk Handling

- Missing optional systems are represented as `not_available`, never fake
  metrics.
- The runner does not import or call training code.
- The runner does not use network, GPU, model weights, adapters, or private
  paths.
- Final-test access is visible in the run manifest and no-retune pledge.
