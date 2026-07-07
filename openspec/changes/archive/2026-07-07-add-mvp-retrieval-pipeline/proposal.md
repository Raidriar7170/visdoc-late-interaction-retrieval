## Why

The repository has deterministic text and visual-smoke diagnostics, but they are
still separate report surfaces. A minimal end-to-end MVP pipeline is needed so a
clean checkout can run one command and produce reviewer-readable rankings,
metrics, run evidence, and explicit diagnostic-only boundaries.

## What Changes

- Add a config-driven MVP command,
  `PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json`,
  for the fixed synthetic smoke corpus.
- Reuse the existing manifest-backed synthetic corpus and explicit candidate
  universe semantics.
- Run text baselines (`bm25`, `lexical_cosine`, and cheap RRF hybrids where
  configured) and a visual late-interaction diagnostic scaffold.
- Add a `VisualRetriever` protocol, deterministic CPU-only
  `MockVisualRetriever`, MaxSim scoring, and JSON cache round-trip support for
  mock query/page token embeddings.
- Emit MVP artifacts under `reports/mvp/`: metrics, rankings, run card, and
  cache evidence.
- Add a concise Chinese/English reviewer-readable human brief and a progress
  ledger MVP entry.
- Add tests for metrics, MaxSim, shape validation, empty token handling,
  deterministic mock embeddings, cache round-trip, tiny-fixture ranking, MVP
  smoke execution, split/candidate boundary, and ledger parsing.

## Capabilities

### New Capabilities

- `mvp-retrieval-pipeline`: One-command diagnostic page-retrieval MVP pipeline
  over the fixed synthetic smoke corpus with text baselines, visual mock
  late-interaction scaffold, metrics, rankings, run card, human brief, and
  evidence outputs.

### Modified Capabilities

- None.

## Impact

- Affected code: `src/visdoc_retrieve/` MVP CLI/pipeline and visual scaffold
  modules, existing retrieval utilities, and focused tests.
- Affected artifacts: `configs/mvp.json`, `reports/mvp/*`,
  `docs/human-briefs/*`, `reports/progress-ledger.yaml`,
  `.opsx-goal.yaml`, and `.opsx-auto-inbox/*`.
- No new runtime dependency, GPU requirement, network access, model download,
  training, hard-negative mining, final-test evaluation, commit, push, merge,
  deploy, or benchmark-improvement claim is introduced.
