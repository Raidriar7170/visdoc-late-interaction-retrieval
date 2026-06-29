# visual-retrieval-baselines Specification

## ADDED Requirements

### Requirement: Manifest-backed visual smoke corpus
The system SHALL load a visual smoke corpus from Phase 1 page and query
manifests, validate split/family consistency, read page image artifacts, and
keep query relevance metadata available to visual-smoke retrievers and reports.

#### Scenario: Valid visual corpus loads from manifests
- **WHEN** the visual corpus loader is given existing page and query manifests
           plus existing page image artifacts
- **THEN** it returns page and query records keyed by stable IDs with split,
           family, positive page IDs, image bytes, and image-path metadata

#### Scenario: Missing page image fails loading
- **WHEN** a page manifest record points to a missing image artifact
- **THEN** the visual corpus loader fails with a validation error instead of
           silently indexing an empty image

### Requirement: Deterministic local visual-smoke retriever
The system SHALL provide a deterministic local visual-smoke retriever with a
late-interaction-style scoring shape that runs without network access, external
model downloads, GPU hardware, FAISS, or training.

#### Scenario: Visual-smoke ranking is deterministic
- **WHEN** the visual-smoke retriever ranks the same query against the same toy
           page images repeatedly
- **THEN** it returns the same page order and scores with stable page-ID
           tie-breaking

#### Scenario: Visual-smoke retriever is local-only
- **WHEN** local validation constructs the default visual-smoke retriever
- **THEN** it reports that no external model, network, GPU, or training path is
           required

### Requirement: Config-driven visual smoke report
The system SHALL generate a visual-baseline report from a committed config that
declares input manifests, evaluated splits, enabled visual-smoke method, and
output path.

#### Scenario: Visual smoke report is generated from config
- **WHEN** the default visual-baseline config is executed against the synthetic
           smoke corpus
- **THEN** it writes a deterministic diagnostic report containing a
           `visual_smoke` method section with retrieval metrics and diagnostic
           support fields

#### Scenario: Report excludes final test by default
- **WHEN** the default visual-baseline config is inspected or executed
- **THEN** the final test split is recorded as `not_run` and is not used for
           reported metric values

### Requirement: Visual smoke boundary
The visual baseline layer SHALL remain diagnostic-only and SHALL NOT claim real
ColPali/ColQwen performance, benchmark improvement, hard-negative mining
quality, training results, or final-test performance.

#### Scenario: Report wording remains diagnostic
- **WHEN** the visual smoke report is generated
- **THEN** it records local-only boundary flags for no network, no GPU, no
           external model download, no hard-negative triples, no training, no
           final-test evaluation, and no benchmark claim
