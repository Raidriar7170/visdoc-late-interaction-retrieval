# VisDoc-Retrieve Project Card

## Problem

Visually rich PDFs and scanned technical documents often contain layout,
figures, tables, and OCR failure cases that pure text retrieval can miss. This
project asks whether a disciplined document-retrieval pipeline can compare
lexical baselines, visual late-interaction scaffolds, hard-negative mining, and
future adapter training under a reproducible evidence contract.

## Approach

The project builds a page-level retrieval workflow around a synthetic smoke
corpus with explicit train/dev/test splits, candidate-universe metadata, and
frozen evaluation metrics. It starts with deterministic text baselines, adds a
mock visual MaxSim scaffold, prepares hard-negative and training-readiness
artifacts, records A100/runtime gates, and finishes with a one-time frozen
final comparison plus no-retune pledge.

## Systems Compared

Final comparison systems that ran:

- `bm25`
- `lexical_cosine`
- `bm25_lexical_rrf`
- `mock_visual`

Systems reported as unavailable:

- `tiny_lora_adapter`: `not_available`; no adapter checkpoint was committed.
- `zero_shot_visual_backend`: `not_available`; no real visual backend metrics
  were fabricated.

The `mock_visual` system is a deterministic scaffold for MaxSim plumbing. It is
not real visual model performance.

## Engineering Artifacts

- Data manifests and synthetic smoke corpus with split metadata.
- Candidate-universe and retrieval-metric contracts.
- Deterministic BM25, lexical cosine, RRF, and mock visual MaxSim diagnostics.
- Hard-negative mining over train/dev only.
- Training readiness and pilot safety gates with blocked/default-safe behavior.
- A100 runtime/model-path evidence and a reviewed `max_steps=1` /
  `sample_limit=1` tiny runner proof.
- Dev-only pilot evaluation harness with missing-adapter status handling.
- Frozen final-comparison protocol, execution dry-run gate, one-time final run,
  final metrics, claim checklist, and no-retune pledge.

## Final Result Boundary

The Phase 6D final comparison is complete, and the final test was read once
under the frozen protocol. The final claim checklist says
`no_clear_improvement_claim`; this project should not be presented as a
benchmark improvement result.

The strongest defensible claim is engineering-oriented: the project produced a
reproducible, evidence-rich retrieval evaluation pipeline with clear gates,
honest unavailable-system handling, and a no-retune final benchmark discipline.

## What I Learned

- A retrieval benchmark is only credible when data splits, candidate universe,
  metrics, and claim boundaries are frozen before final access.
- Visual late interaction needs real model artifacts and backend execution
  before it can be claimed as visual-model performance.
- Tiny GPU runner proofs are useful for pipeline confidence but should remain
  separate from benchmark results.
- Negative or mixed final results are still valuable when the evaluation
  contract prevents result-driven tuning.

## Evidence Links

- Final report:
  `reports/final-comparison/final-comparison-report.md`
- Final run manifest:
  `reports/final-comparison/final-comparison-run-manifest.json`
- Final metrics:
  `reports/final-comparison/final-metrics.json`
- Claim checklist:
  `reports/final-comparison/final-claim-checklist.json`
- No-retune pledge:
  `reports/final-comparison/no-retune-pledge.md`
- Evidence index:
  `docs/evidence-index.md`
- Final comparison protocol:
  `docs/final-comparison-protocol.md`
