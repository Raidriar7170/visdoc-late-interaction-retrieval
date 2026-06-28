## ADDED Requirements

### Requirement: Page manifest schema
The system SHALL define a page manifest record with `page_id`, `doc_id`, `page_number`,
`image_path`, `text_path`, `family_id`, `split`, and `content_hash`.

#### Scenario: Valid page record passes validation
- **WHEN** a generated page manifest record contains all required fields with
           repo-relative paths and a hexadecimal SHA-256 content hash
- **THEN** page manifest validation succeeds

#### Scenario: Invalid page record fails validation
- **WHEN** a page manifest record omits a required field or uses an invalid split
- **THEN** page manifest validation fails with a validation error

### Requirement: Query relevance schema
The system SHALL define a query relevance record with `query_id`, `query`,
`positive_page_ids`, `family_id`, `split`, `query_type`, and `source` metadata.

#### Scenario: Valid query record passes validation
- **WHEN** a generated query record references one or more known positive pages from the
           same family and split
- **THEN** query manifest validation succeeds

#### Scenario: Invalid query record fails validation
- **WHEN** a query record references an unknown page, an invalid split, an invalid query
           type, or a positive page from a different split
- **THEN** query manifest validation fails with a validation error

### Requirement: Manifest file format
The system SHALL write page and query manifests as deterministic UTF-8 JSONL files
sorted by stable IDs.

#### Scenario: Manifest ordering is deterministic
- **WHEN** the same corpus is generated twice with the same configuration
- **THEN** the page and query manifest files have identical SHA-256 digests

### Requirement: Split leakage guard
The system SHALL expose a validation-only guard that rejects training candidate page IDs
containing pages from the final test split.

#### Scenario: Test page leakage is rejected
- **WHEN** a training candidate page list includes any page whose manifest split is
           `test`
- **THEN** the leakage guard fails with a validation error

#### Scenario: Non-test candidates pass leakage guard
- **WHEN** a training candidate page list contains only `train` or configured non-test
           page IDs
- **THEN** the leakage guard succeeds

### Requirement: No retrieval result surface
The data format layer SHALL NOT compute retrieval scores, ranking metrics, hard-negative
triples, model embeddings, or benchmark result tables.

#### Scenario: Data validation remains retrieval-free
- **WHEN** Phase 1 validation runs
- **THEN** it validates schemas, hashes, splits, and leakage boundaries without
           producing retrieval scores or final benchmark metrics
