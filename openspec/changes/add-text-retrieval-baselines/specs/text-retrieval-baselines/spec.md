## ADDED Requirements

### Requirement: Manifest-backed text retrieval corpus
The system SHALL load text retrieval corpora from Phase 1 page and query
manifests, validate the records, resolve repo-relative page text artifacts, and
keep page/query split metadata available to retrievers and reports.

#### Scenario: Valid text corpus loads from manifests
- **WHEN** the text baseline loader is given existing Phase 1 page and query manifests
           plus existing text artifacts
- **THEN** it returns page and query records keyed by stable IDs with their split,
           family, query type, positive page IDs, and page text available for retrieval

#### Scenario: Missing page text fails loading
- **WHEN** a page manifest record points to a missing text artifact
- **THEN** the text baseline loader fails with a validation error instead of silently
           indexing an empty page

### Requirement: Deterministic BM25 retriever
The system SHALL provide a BM25 retriever over page text with deterministic
tokenization, scoring, ranking, and stable tie-breaking by page ID.

#### Scenario: BM25 ranks exact lexical matches first
- **WHEN** a toy corpus contains one page that shares the query's distinctive tokens and
           another page that does not
- **THEN** the BM25 retriever ranks the lexical match ahead of the non-match

#### Scenario: BM25 tie-breaking is stable
- **WHEN** two pages receive the same BM25 score for a query
- **THEN** their relative order is deterministic and sorted by stable page ID

### Requirement: Deterministic dense-text baseline
The system SHALL provide a local deterministic dense-text baseline that can run
in tests and smoke reports without network access, GPU hardware, external model
downloads, or FAISS.

#### Scenario: Dense baseline runs in local validation
- **WHEN** local validation builds the default dense-text index for a toy corpus
- **THEN** it produces deterministic vectors and rankings without downloading an
           embedding model or requiring a GPU

#### Scenario: Optional embedding model path is disabled by default
- **WHEN** the default text baseline config is used
- **THEN** external sentence-transformer, BGE-family, or FAISS-backed execution paths
           are not required to generate the smoke report

### Requirement: Hybrid reciprocal-rank fusion retriever
The system SHALL provide a hybrid retriever that combines BM25 and dense-text
rankings with reciprocal rank fusion and deterministic page-ID tie-breaking.

#### Scenario: RRF combines sparse and dense rankings
- **WHEN** BM25 and dense baselines return different top-ranked pages for the same query
- **THEN** the hybrid retriever produces a fused ranking using reciprocal rank positions
           from both baselines

#### Scenario: Hybrid tie-breaking is stable
- **WHEN** two pages receive the same fused RRF score
- **THEN** their relative order is deterministic and sorted by stable page ID

### Requirement: Text-only baseline boundary
The text retrieval baseline layer SHALL NOT read page images, run visual
late-interaction models, emit hard-negative triples, train adapters, or evaluate
the final test split by default.

#### Scenario: Baseline execution remains text-only
- **WHEN** the default text baseline report is generated
- **THEN** it consumes page text artifacts and manifests without invoking ColPali,
           ColQwen, image embeddings, hard-negative mining, LoRA/QLoRA training, GPU
           hardware, or final test evaluation
