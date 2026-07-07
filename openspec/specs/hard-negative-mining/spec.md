# hard-negative-mining Specification

## Purpose
TBD - created by archiving change add-hard-negative-mining. Update Purpose after archive.
## Requirements
### Requirement: One-command hard-negative mining
The system SHALL provide a config-driven hard-negative mining command that runs
locally from a clean checkout and writes deterministic train/dev mining
artifacts.

#### Scenario: Default mining command writes required artifacts
- **WHEN** `PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives --config configs/hard_negatives.json` is run from the repository root
- **THEN** the command writes `data/derived/hard_negatives/train.jsonl`,
  `data/derived/hard_negatives/dev.jsonl`,
  `reports/hard-negatives/mining-summary.json`,
  `reports/hard-negatives/leakage-check.json`, and
  `reports/hard-negatives/run-card.md`

#### Scenario: Mining stays local and CPU-only
- **WHEN** the default mining config is run
- **THEN** it requires no network access, GPU hardware, model download, external
  embedding service, training run, final-test evaluation, deployment, or
  benchmark-improvement claim

### Requirement: Supported and unsupported negative source reporting
The miner SHALL attempt the configured local negative sources and SHALL record
per-source support, unsupported status, and evidence without fabricating
candidates.

#### Scenario: Local ranker sources emit wrong-page negatives
- **WHEN** BM25, lexical cosine, available RRF/hybrid text ranking, and
  deterministic mock visual MaxSim sources produce ranked pages for a query
- **THEN** the miner emits only top-k wrong-page negatives from those rankings
  and records the source, rank, score, and candidate universe for each record

#### Scenario: Metadata sources report support honestly
- **WHEN** same-document or tag-aware metadata support exists for a query
- **THEN** the miner emits matching wrong-page negatives with evidence
- **WHEN** metadata support is absent for a configured source
- **THEN** the mining summary records `support: 0` or a `null` evidence field for
  that source instead of inventing negatives

### Requirement: Hard-negative record schema
Every emitted hard-negative record SHALL contain the fields needed for later
training-preparation review and deterministic round-trip loading.

#### Scenario: Required fields are present
- **WHEN** a hard-negative JSONL record is inspected
- **THEN** it contains `query_id`, `positive_page_id`, `negative_page_id`,
  `split`, `negative_source`, `rank`, `score`, `candidate_universe_id`, and
  `reason` or `evidence`

#### Scenario: JSONL output is deterministic
- **WHEN** the same mining command is run twice with the same config and inputs
- **THEN** the train/dev JSONL outputs contain the same records in the same order
  and duplicate candidates are removed deterministically

### Requirement: Split leakage checks
The miner SHALL prove that hard-negative artifacts do not leak positives or
final-test data into train/dev mining outputs.

#### Scenario: Negatives never equal query positives
- **WHEN** leakage checks inspect train/dev hard-negative records
- **THEN** `negative_page_id` is never equal to any positive page for the same
  query

#### Scenario: Train and dev query boundaries are enforced
- **WHEN** train triples are inspected
- **THEN** they contain no dev or test `query_id`
- **WHEN** dev triples are inspected
- **THEN** they contain no test `query_id`

#### Scenario: Final test split never appears in training artifacts
- **WHEN** the hard-negative output files and leakage report are inspected
- **THEN** the test split never appears in train/dev artifacts and final-test
  evaluation is recorded as `not_run`

### Requirement: Review evidence and project ledger
The miner SHALL write reviewer-readable evidence that explains inputs, outputs,
source support, leakage checks, deterministic status, and remaining boundaries.

#### Scenario: Summary and run card identify boundaries
- **WHEN** `reports/hard-negatives/mining-summary.json` and
  `reports/hard-negatives/run-card.md` are inspected
- **THEN** they identify input manifests, evaluated splits, candidate universe,
  enabled sources, unsupported sources, CPU-only deterministic status, and the
  no-training/no-final-test/no-benchmark-claim boundary

#### Scenario: Human brief and ledger are updated
- **WHEN** the Phase 4 artifacts are inspected
- **THEN** a concise Chinese human brief exists under `docs/human-briefs/` and
  `reports/progress-ledger.yaml` contains a hard-negative mining checkpoint entry
  without claiming training, real visual model improvement, or final-test
  performance

### Requirement: Existing MVP behavior remains unchanged
The hard-negative mining checkpoint SHALL NOT change the default deterministic
MVP pipeline behavior or reinterpret `mock_visual` as real visual retrieval.

#### Scenario: MVP command still works
- **WHEN** `PYTHONPATH=src python -m visdoc_retrieve.run_mvp --config configs/mvp.json` is run after mining support is added
- **THEN** the MVP command succeeds with its existing deterministic mock visual
  surface and does not require hard-negative mining, model downloads, GPU
  hardware, or final-test evaluation
