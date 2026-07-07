## ADDED Requirements

### Requirement: Training-readiness config
The system SHALL provide local-only training-readiness configs that declare
model identity placeholders, local model path checks, adapter output location,
hard-negative inputs, corpus/query/qrels inputs, candidate-universe identity,
loss/training hyperparameters, device, dry-run mode, and final-test permission.

#### Scenario: Dry-run config parses locally
- **WHEN** `configs/train_lora_dry_run.json` is loaded
- **THEN** it records the configured hard-negative, corpus, query, qrels,
  candidate-universe, loss, batch-size, accumulation, max-steps, learning-rate,
  seed, device, dry-run, and `allow_final_test=false` fields without requiring
  torch, GPU hardware, model downloads, network access, or local model weights

#### Scenario: Final test remains disabled
- **WHEN** a training-readiness config sets `allow_final_test` to true
- **THEN** Phase 5A validation rejects the config instead of evaluating or
  freezing final-test metrics

### Requirement: Hard-negative triple loader
The system SHALL load Phase 4 train/dev hard-negative JSONL artifacts and
produce deterministic query/positive_page/negative_page triples after schema,
split, candidate-universe, and leakage validation.

#### Scenario: Train and dev triples load deterministically
- **WHEN** the default train and dev hard-negative artifacts are loaded with
  `candidate_universe_id` set to `evaluated_split_pages`
- **THEN** the loader emits deterministic triples for train and dev records in
  stable order and can apply a deterministic dry-run sample limit

#### Scenario: Split leakage is rejected
- **WHEN** a train readiness record references a dev or test query/page, or a
  dev readiness record references a test query/page
- **THEN** the loader fails with a validation error before any mock batch is
  constructed

#### Scenario: Candidate-universe mismatch is rejected
- **WHEN** a hard-negative record has a `candidate_universe_id` different from
  the configured readiness candidate universe
- **THEN** the loader fails with a validation error

#### Scenario: Negative equal to positive is rejected
- **WHEN** a hard-negative record has `negative_page_id` equal to the
  `positive_page_id` or another positive page for the same query
- **THEN** the loader fails with a validation error

### Requirement: Mock ranking loss smoke
The system SHALL provide a CPU-safe mock scorer and contrastive/ranking loss
smoke surface that validates shapes, handles empty batches, and demonstrates
that batches where positive scores exceed negative scores produce lower loss.

#### Scenario: Positive margin lowers mock loss
- **WHEN** a mock batch has positive scores above negative scores by a larger
  margin than another valid batch
- **THEN** the computed mock ranking loss is lower for the better-ranked batch

#### Scenario: Invalid batch shapes fail
- **WHEN** mock positive and negative score lists have mismatched lengths
- **THEN** the loss function fails with a validation error

#### Scenario: Empty batch is explicit
- **WHEN** the mock loss receives an empty batch
- **THEN** it returns an explicit empty-batch result without requiring torch,
  GPU hardware, or model libraries

### Requirement: Dry-run trainer scaffold
The system SHALL expose a dry-run trainer command that performs config parsing,
artifact hashing, dataset loading, leakage checks, mock batch construction,
mock loss computation, and report generation without executing training.

#### Scenario: Default dry-run command writes readiness artifacts
- **WHEN** `PYTHONPATH=src python -m visdoc_retrieve.train_lora_dry_run --config configs/train_lora_dry_run.json` is run from the repository root
- **THEN** it writes `reports/training-readiness/artifact-freeze.json`,
  `reports/training-readiness/dataset-summary.json`,
  `reports/training-readiness/dry-run-card.md`, and
  `reports/training-readiness/safety-check.json`

#### Scenario: Dry-run does not create adapters
- **WHEN** the default dry-run command is run
- **THEN** no model weights, adapter checkpoints, embedding caches, benchmark
  result tables, final-test metrics, or real training outputs are created

### Requirement: Artifact freeze and safety evidence
The system SHALL record artifact hashes, candidate-universe identity, split
policy, metric-definition references, model revision placeholder/configured
value, timestamp, final-test exclusion, and explicit safety checks for Phase
5A review.

#### Scenario: Freeze records input hashes and boundaries
- **WHEN** `artifact-freeze.json` is inspected after the default dry run
- **THEN** it contains paths and SHA-256 hashes for train/dev hard negatives,
  corpus, query, and qrels-style inputs; records the candidate universe, split
  policy, metric definition reference, model revision value, timestamp, and
  states that final test data was not used

#### Scenario: Safety check records no-training boundary
- **WHEN** `safety-check.json` is inspected after the default dry run
- **THEN** it explicitly records that final test was not used, training was not
  executed, model download was not executed, GPU was not required, no model
  weights were committed, no adapter checkpoint was committed, no benchmark
  claim was added, and mock/dry-run results are not model performance

### Requirement: Project evidence and prior behavior preservation
The training-readiness checkpoint SHALL add reviewer-readable evidence while
preserving the existing MVP command, hard-negative mining command, optional
visual backend import safety, and diagnostic-only claims.

#### Scenario: Human brief and ledger describe Phase 5A
- **WHEN** Phase 5A artifacts are inspected
- **THEN** a concise Chinese human brief under `docs/human-briefs/` and a
  `reports/progress-ledger.yaml` Phase 5A entry explain readiness status,
  hard-negative triple flow, artifact freeze evidence, dry-run checks, remaining
  future work, and no-training/no-final-test/no-benchmark-claim boundaries

#### Scenario: Existing CLIs remain valid
- **WHEN** the MVP command and hard-negative mining command are run after
  Phase 5A readiness support is added
- **THEN** both commands still succeed with their existing deterministic local
  behavior and do not require torch, GPU hardware, model downloads, final-test
  evaluation, or real training
