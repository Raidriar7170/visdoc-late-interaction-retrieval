## Why

Phase 2 text diagnostics currently report strong scores over a small dev-only
candidate pool, while the existing `dense_text` label actually describes a
local lexical-vector cosine baseline rather than a neural embedding baseline.
Before moving to Phase 4/5 visual models, the project needs Phase 2.5 to make
the text baseline names and candidate universe explicit so later wins cannot be
mistaken for a larger retrieval or neural-model improvement.

## What Changes

- Rename the current deterministic local `dense_text` method contract to a
  lexical cosine / local TF-IDF cosine baseline name in code, config, reports,
  specs, tests, ledgers, and docs.
- Add an explicit retrieval candidate universe contract that records whether a
  report ranks over evaluated-split pages, non-train pages, or all pages.
- Keep the existing synthetic smoke diagnostic report local-only and
  CPU-only, with no new data and no final-test evaluation.
- Add a config-gated neural text baseline contract for a future BGE-M3 or
  sentence-transformers dense method, but require local validation to use a
  mock or deterministic stub embedding path unless an explicit later phase
  enables real external embeddings.
- Add a BM25 + neural RRF hybrid contract that stays disabled by default until
  the neural baseline is explicitly enabled.
- Preserve all current Phase 3A boundaries: synthetic corpus, text diagnostic
  baselines, and local visual-smoke diagnostics exist; real ColPali/ColQwen,
  external embeddings, hard negatives, training, and final test evaluation
  remain not started.

## Capabilities

### New Capabilities

- `retrieval-candidate-universe`: Declares and reports the candidate page pool
  used by retrieval diagnostics, including evaluated-split, non-train, and
  all-pages universes.

### Modified Capabilities

- `text-retrieval-baselines`: Rename the current local lexical-vector
  `dense_text` baseline, add a config-gated neural text baseline contract, and
  define BM25+neural RRF behavior without enabling external model downloads by
  default.
- `retrieval-evaluation-metrics`: Require diagnostic reports to expose the
  candidate universe and rank support so metric values are not interpreted
  without knowing the retrieval pool size.

## Impact

- Affected code will be limited to `src/visdoc_retrieve/`, `tests/`,
  `configs/`, `reports/`, `README.md`, `AGENTS.md`, `configs/README.md`,
  `reports/progress-ledger.yaml`, and the OpenSpec artifacts for this change.
- No new corpus data, page/query manifests, hard-negative triples, model
  checkpoints, adapters, embedding caches, final benchmark tables, or final
  test results are introduced.
- Validation remains local-only and CPU-only through the existing pytest,
  ruff, mypy, OpenSpec, compile, and diff checks.
