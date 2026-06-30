# VisDoc MVP Diagnostic Run Card

Status: diagnostic smoke only.

Command:

```bash
PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json
```

Inputs:
- Pages manifest: data/synthetic-smoke/pages.jsonl
- Queries/qrels manifest: data/synthetic-smoke/queries.jsonl
- Evaluated split: dev
- Candidate universe: evaluated_split_pages
- Candidate pages: 8
- Evaluated queries: 24

Methods:
- bm25: deterministic text baseline.
- lexical_cosine: deterministic local lexical cosine baseline.
- bm25_lexical_rrf: deterministic reciprocal-rank fusion of BM25 and lexical cosine.
- mock_visual: deterministic mock scaffold using MaxSim over query/page token
  embeddings.

Visual boundary:
The visual late-interaction path is a deterministic mock scaffold and is not real ColPali or ColQwen execution.

Claims:
Metrics are diagnostic smoke evidence only. They are not final benchmark results,
retrieval improvement claims, model superiority claims, frozen-test claims, or
production readiness claims.

Not started:
- real ColPali / ColQwen execution
- external embeddings
- hard-negative mining
- LoRA / QLoRA training
- final test evaluation

Evidence:
- Metrics: reports/mvp/metrics.json
- Rankings: reports/mvp/rankings.csv
- Mock visual cache: reports/mvp/mock-visual-embeddings.json
- Human brief: docs/human-briefs/2026-06-30-visdoc-mvp.html
