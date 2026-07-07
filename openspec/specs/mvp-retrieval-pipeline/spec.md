# mvp-retrieval-pipeline Specification

## Purpose
TBD - created by archiving change add-mvp-retrieval-pipeline. Update Purpose after archive.
## Requirements
### Requirement: One-command MVP pipeline
The system SHALL provide a config-driven MVP command that runs the fixed
synthetic smoke page-retrieval pipeline from a clean checkout and writes a
deterministic diagnostic evidence bundle.

#### Scenario: MVP command writes required artifacts
- **WHEN** `PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json` is run
  from the repository root
- **THEN** the command writes `reports/mvp/metrics.json`,
  `reports/mvp/rankings.csv`, `reports/mvp/run-card.md`, and cache evidence
  under `reports/mvp/`

#### Scenario: MVP command stays local only
- **WHEN** the MVP command runs with the default config
- **THEN** it requires no network access, GPU hardware, external model download,
  external embedding service, training run, hard-negative mining job, or final
  test evaluation

### Requirement: Explicit MVP candidate universe
The MVP pipeline SHALL separate evaluated query splits from candidate page
universe selection and SHALL record candidate page support in every report
surface.

#### Scenario: Default candidate universe ranks dev queries over dev pages
- **WHEN** the default MVP config evaluates the synthetic smoke `dev` split with
  `evaluated_split_pages`
- **THEN** the pipeline ranks 24 dev queries over 8 dev candidate pages and
  records candidate split counts as `{"dev": 8}`

#### Scenario: Final test queries are not evaluated
- **WHEN** the default MVP pipeline finishes
- **THEN** the final test split is recorded as `not_run` and no final-test query
  contributes to reported metrics

### Requirement: Text baselines in MVP
The MVP pipeline SHALL run deterministic text baselines over the configured
candidate page universe, including BM25, lexical cosine, and configured RRF
hybrids when available.

#### Scenario: Text methods produce rankings and metrics
- **WHEN** the MVP pipeline runs the default config
- **THEN** it records rankings and metrics for `bm25`, `lexical_cosine`, and
  `bm25_lexical_rrf`

#### Scenario: Text methods do not imply external dense embeddings
- **WHEN** MVP text method metadata is inspected
- **THEN** lexical cosine is not named `dense_text`, and no BGE,
  sentence-transformers, FAISS, external embedding cache, network, GPU, or model
  download path is required

### Requirement: Visual late-interaction mock scaffold
The MVP pipeline SHALL include a `VisualRetriever` protocol, deterministic
`MockVisualRetriever`, and MaxSim scoring over query token embeddings and page
token embeddings.

#### Scenario: Mock visual ranking is deterministic
- **WHEN** the mock visual retriever ranks the same query against the same page
  fixtures repeatedly
- **THEN** it returns identical scores and stable page-ID tie-breaking

#### Scenario: MaxSim handles valid and empty token sets
- **WHEN** MaxSim receives valid equal-width token embeddings
- **THEN** it returns the mean of each query token's best page-token similarity
- **WHEN** either query tokens or page tokens are empty
- **THEN** it returns `0.0`

#### Scenario: MaxSim rejects shape mismatches
- **WHEN** MaxSim receives token embeddings with inconsistent dimensions
- **THEN** it raises a validation error instead of silently producing a score

### Requirement: Mock embedding cache schema
The MVP visual scaffold SHALL persist and reload deterministic mock query/page
token embeddings with schema metadata and shape information.

#### Scenario: Mock cache round-trips
- **WHEN** mock visual embeddings are written to cache and loaded again
- **THEN** the loaded cache matches the original page IDs, query IDs, vector
  dimensions, token counts, and embedding values

#### Scenario: Cache metadata states diagnostic provenance
- **WHEN** the MVP cache metadata is inspected
- **THEN** it records `schema_version`, `retriever_id`,
  `provider: deterministic_mock`, and false external/network/GPU/model-download
  flags

### Requirement: MVP metrics and subset support
The MVP pipeline SHALL compute Recall@1, Recall@5, MRR, and NDCG@10 overall and
by query-type subset where support exists.

#### Scenario: MVP metrics include core retrieval metrics
- **WHEN** the MVP pipeline writes `reports/mvp/metrics.json`
- **THEN** every method contains Recall@1, Recall@5, MRR, NDCG@10, evaluated
  query count, and ranked pages per query

#### Scenario: Zero-support subsets are not fabricated
- **WHEN** a configured subset has no matching queries
- **THEN** the subset entry records `support: 0` and `metrics: null`

### Requirement: MVP run card, human brief, and ledger evidence
The MVP pipeline SHALL write reviewer-readable evidence that explains inputs,
candidate universe, methods, diagnostic status, reproduction command, and
non-goals.

#### Scenario: Run card and human brief identify mock visual status
- **WHEN** the MVP run card and human brief are inspected
- **THEN** they state that the visual late-interaction path is a deterministic
  mock scaffold and not real ColPali or ColQwen execution

#### Scenario: Ledger records MVP without overstating results
- **WHEN** `reports/progress-ledger.yaml` is parsed after the MVP phase
- **THEN** it contains an MVP entry with evidence paths and records real visual
  model execution, external embeddings, hard-negative mining, training, and
  final test evaluation as not started or not run
