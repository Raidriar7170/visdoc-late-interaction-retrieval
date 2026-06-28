# synthetic-corpus-generation Specification

## Purpose
Defines the deterministic synthetic technical document corpus used as a local
smoke fixture for page images, OCR-like text artifacts, manifests, family
splits, and hash stability.
## Requirements
### Requirement: Deterministic synthetic corpus generation
The system SHALL generate a deterministic synthetic technical corpus for smoke testing with 3 document families, 24 pages total, and 72 query relevance records.

#### Scenario: Corpus size matches Phase 1 smoke contract
- **WHEN** the default synthetic corpus generator runs
- **THEN** it writes manifests containing exactly 3 document families, 24 page records, and 72 query records

### Requirement: Technical page variety
The synthetic corpus SHALL include table, figure, flow diagram, specification, troubleshooting, layout, OCR-failure-style, and mixed Chinese/English page/query signals.

#### Scenario: Query types cover required visual cases
- **WHEN** the generated query manifest is validated
- **THEN** it includes the query types `text`, `table`, `figure`, `layout`, and `ocr_failure`

### Requirement: Page artifact generation
The generator SHALL create a PDF per document family plus rendered page image artifacts and OCR-like text artifacts for every page.

#### Scenario: Page artifacts exist
- **WHEN** the synthetic corpus is generated
- **THEN** every page manifest record points to an existing page image artifact and text artifact under the generated corpus directory

### Requirement: Family-based split contract
The generator SHALL assign each document family to exactly one split and SHALL keep page and query splits consistent with family assignment.

#### Scenario: Split is family-consistent
- **WHEN** the generated manifests are validated
- **THEN** all records from a family share one split and every query positive page belongs to the same split as the query

### Requirement: Content hash stability
The generator SHALL compute content hashes from generated page image and text artifacts so unchanged regenerated pages have stable hashes.

#### Scenario: Repeated generation is stable
- **WHEN** the generator runs twice into separate output directories
- **THEN** the generated page records, query records, and corpus summary have matching content hashes and manifest digests

### Requirement: No model or benchmark dependency
The synthetic corpus generator SHALL NOT require GPU hardware, model downloads, embeddings, retrieval models, ranking metrics, or A100 access.

#### Scenario: Corpus generation is local-only
- **WHEN** the corpus generator runs in tests
- **THEN** it completes using local CPU document generation and rendering dependencies only
