# Phase 6D Final Comparison Report

Status: one-time frozen final comparison complete.

This run read the frozen final-test split exactly once under `phase-6b-final-comparison-protocol/v1`. No tuning, training, retrieval pipeline change, metric-definition change, candidate-universe change, or final-label change is allowed after this run.

## Systems

- `bm25`: Recall@1=0.6666666666666666, Recall@5=0.9166666666666666, MRR=0.7687499999999999, NDCG@10=0.8238302057361316; support=24
- `bm25_lexical_rrf`: Recall@1=0.6666666666666666, Recall@5=0.875, MRR=0.7715773809523809, NDCG@10=0.8261863006672855; support=24
- `lexical_cosine`: Recall@1=0.6666666666666666, Recall@5=0.9166666666666666, MRR=0.7747023809523809, NDCG@10=0.8291607977693193; support=24
- `mock_visual`: Recall@1=0.125, Recall@5=0.5, MRR=0.3368055555555555, NDCG@10=0.4911261260454174; support=24
- `tiny_lora_adapter`: not_available; metrics not fabricated.
- `zero_shot_visual_backend`: not_available; metrics not fabricated.

## Claim Boundary

No clear benchmark improvement claim is supported. The run compares deterministic text baselines and a deterministic mock visual scaffold. Tiny A100 runner proof and dev-only evidence remain non-final pipeline evidence.

## Evidence

- Manifest: `reports/final-comparison/final-comparison-run-manifest.json`
- Metrics: `reports/final-comparison/final-metrics.json`
- Rankings: `reports/final-comparison/final-rankings.csv`
- Claim checklist: `reports/final-comparison/final-claim-checklist.json`
- No-retune pledge: `reports/final-comparison/no-retune-pledge.md`
