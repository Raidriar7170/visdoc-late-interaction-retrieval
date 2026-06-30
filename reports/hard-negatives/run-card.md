# VisDoc Hard-Negative Mining Run Card

Status: hard-negative mining checkpoint, deterministic local smoke data.

Command:

```bash
PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives --config configs/hard_negatives.json
```

Inputs:
- Pages manifest: data/synthetic-smoke/pages.jsonl
- Queries/qrels manifest: data/synthetic-smoke/queries.jsonl
- Evaluated splits: train, dev
- Candidate universe: evaluated_split_pages
- final test evaluation: not_run

Outputs:
- Train triples: data/derived/hard_negatives/train.jsonl
- Dev triples: data/derived/hard_negatives/dev.jsonl
- Summary: reports/hard-negatives/mining-summary.json
- Leakage check: reports/hard-negatives/leakage-check.json

Counts:
- Total records: 858
- Train records: 429
- Dev records: 429

Sources:
- bm25: status=generated, support=144
- bm25_lexical_rrf: status=generated, support=144
- lexical_cosine: status=generated, support=144
- mock_visual: status=generated, support=144
- same_document: status=generated, support=144
- tag_aware: status=generated, support=138

Boundaries:
- no training
- no final test evaluation
- no model download
- no GPU requirement
- no real ColPali / ColQwen execution
- no benchmark improvement claim
- no RAG or chatbot behavior
