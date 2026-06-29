## ADDED Requirements

### Requirement: Candidate universe metric context
The baseline report SHALL include candidate universe context with every metric
surface so retrieval scores cannot be interpreted without the retrieval pool
size.

#### Scenario: Metrics include candidate universe context
- **WHEN** a text baseline report is generated
- **THEN** the report includes candidate universe name, candidate page count,
           candidate split counts, evaluated query count, and ranked pages per
           query alongside retrieval metrics

#### Scenario: Smaller candidate pools are labeled diagnostic
- **WHEN** a report evaluates dev queries against only dev pages
- **THEN** the report labels the candidate universe as evaluated-split pages
           and does not present the scores as final benchmark results

### Requirement: Neural text report boundary
The baseline report SHALL distinguish lexical cosine, neural text, BM25+lexical
RRF, and BM25+neural RRF methods without implying external embeddings were used
when they were not enabled.

#### Scenario: Neural provider status is reported
- **WHEN** a neural text method is present in the report
- **THEN** the method records whether the provider is a local stub, mock
           embedding, or explicitly enabled external embedding provider

#### Scenario: External embedding status remains false by default
- **WHEN** the default local validation report is generated
- **THEN** external embedding paths, model downloads, network access, GPU
           requirements, and embedding caches are all reported as disabled or
           absent

## MODIFIED Requirements

### Requirement: Config-driven baseline report
The system SHALL generate a text-baseline report from a committed config that
declares input manifests, evaluated splits, candidate universe, enabled
methods, provider settings, and output paths.

#### Scenario: Smoke report is generated from config
- **WHEN** the default text baseline config is executed against the synthetic
           smoke corpus
- **THEN** it writes a deterministic diagnostic report containing BM25, lexical
           cosine, candidate-universe context, and configured hybrid method
           sections

#### Scenario: Report excludes final test by default
- **WHEN** the default text baseline config is inspected or executed
- **THEN** the final test split is recorded as `not_run` and final-test queries
           are not used for reported metric values

### Requirement: No benchmark improvement claim
The text-baseline evaluation surface SHALL NOT claim visual retriever
performance, neural-model improvement, candidate-universe improvement, or final
benchmark results.

#### Scenario: Report wording remains diagnostic
- **WHEN** Phase 2.5 reporting artifacts are generated
- **THEN** they describe text-baseline and candidate-universe diagnostics
           without claiming ColPali/ColQwen results, adapter improvements,
           neural embedding wins, candidate-pool wins, or final test benchmark
           performance
