## ADDED Requirements

### Requirement: Retrieval ranking metrics
The system SHALL compute Recall@1, Recall@5, MRR, and NDCG@10 for page-level
retrieval rankings against one or more positive page IDs per query.

#### Scenario: Metrics match toy ranking expectations
- **WHEN** toy query rankings contain known positive page positions
- **THEN** Recall@1, Recall@5, MRR, and NDCG@10 match deterministic expected values

#### Scenario: Metrics include support counts
- **WHEN** metrics are computed for a split
- **THEN** the result includes the number of evaluated queries and the number of pages
           ranked per query

### Requirement: Config-driven baseline report
The system SHALL generate a text-baseline report from a committed config that
declares input manifests, evaluated splits, enabled methods, and output paths.

#### Scenario: Smoke report is generated from config
- **WHEN** the default text baseline config is executed against the synthetic smoke
           corpus
- **THEN** it writes a deterministic diagnostic report containing BM25, dense-text, and
           hybrid/RRF method sections

#### Scenario: Report excludes final test by default
- **WHEN** the default text baseline config is inspected or executed
- **THEN** the final test split is recorded as `not_run` and is not used for reported
           metric values

### Requirement: Diagnostic latency and index-size fields
The baseline report SHALL include latency/query and index-size diagnostics for
each enabled method without treating those diagnostics as final benchmark
claims.

#### Scenario: Diagnostic fields are present
- **WHEN** the text baseline report is generated
- **THEN** each enabled method includes latency/query and index-size fields with
           diagnostic labels

### Requirement: Conditional hard-negative hit-rate status
The baseline report SHALL represent hard-negative hit rate only when
hard-negative triples are supplied, and SHALL otherwise mark the metric as not
available with zero hard-negative support.

#### Scenario: Hard-negative metric is unavailable without triples
- **WHEN** the text baseline report is generated before hard-negative mining exists
- **THEN** hard-negative hit rate is marked `not_available` with hard-negative support
           equal to zero

### Requirement: No benchmark improvement claim
The text-baseline evaluation surface SHALL NOT claim visual retriever
performance, model improvement, or final benchmark results.

#### Scenario: Report wording remains diagnostic
- **WHEN** Phase 2 reporting artifacts are generated
- **THEN** they describe text-baseline smoke diagnostics without claiming
           ColPali/ColQwen results, adapter improvements, or final test benchmark
           performance
