# Data

Phase 1 includes a deterministic local smoke corpus at `data/synthetic-smoke/`.
It is a data-format and artifact-generation fixture only, not a retrieval result
surface.

## Synthetic Smoke Corpus

- `pdfs/`: one generated technical PDF per document family.
- `pages/`: rendered PNG page images for every generated PDF page.
- `text/`: OCR-like UTF-8 text artifacts paired with the rendered page images.
- `pages.jsonl`: 24 page manifest records with logical repo-relative paths.
- `queries.jsonl`: 72 query relevance records with stable positive page IDs.
- `summary.json`: counts, family splits, query types, and manifest digests.

Default split contract:

- `manual-a`: train
- `manual-b`: dev
- `manual-c`: test

Boundary: this directory contains no embeddings, retrieval scores, ranking
metrics, hard-negative triples, checkpoints, adapters, benchmark reports, or
final result tables. Phase 2 text-baseline diagnostics consume these manifests
and text artifacts without modifying generated corpus files.

Regenerate the fixture from the repository root with:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path

from visdoc_retrieve.synthetic_corpus import generate_default_corpus

generate_default_corpus(Path("data/synthetic-smoke"))
PY
```
