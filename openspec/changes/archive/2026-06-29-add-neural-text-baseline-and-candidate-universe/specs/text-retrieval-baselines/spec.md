## ADDED Requirements

### Requirement: Deterministic lexical cosine baseline
The system SHALL provide a local deterministic lexical cosine or local TF-IDF
cosine baseline that can run in tests and smoke reports without network access,
GPU hardware, external model downloads, embedding caches, or FAISS.

#### Scenario: Lexical cosine baseline runs in local validation
- **WHEN** local validation builds the default lexical cosine index for a toy
           corpus
- **THEN** it produces deterministic lexical vectors and rankings without
           downloading an embedding model or requiring a GPU

#### Scenario: Lexical cosine name is not neural
- **WHEN** the default text baseline config and report are inspected
- **THEN** the local cosine method is not named `dense_text` and is not
           presented as a BGE, sentence-transformers, or neural embedding
           baseline

### Requirement: Config-gated neural text baseline
The system SHALL provide a neural text baseline interface that can use a local
mock or deterministic stub embedding provider in validation and can represent a
future BGE-M3 or sentence-transformers provider only when explicitly enabled.

#### Scenario: Neural baseline default is local stub
- **WHEN** local validation runs the neural text baseline
- **THEN** it uses a mock or deterministic local embedding provider and records
           that external embeddings are disabled

#### Scenario: External neural provider is disabled by default
- **WHEN** the default text baseline config is used
- **THEN** BGE-M3, sentence-transformers, FAISS, model download, network, and
           GPU execution paths are not required

### Requirement: BM25 plus neural RRF hybrid
The system SHALL provide a separate BM25+neural reciprocal-rank-fusion hybrid
that is distinct from BM25+lexical cosine RRF.

#### Scenario: Neural hybrid method is explicitly named
- **WHEN** a report includes both lexical and neural hybrids
- **THEN** the BM25+neural method ID is distinct from the BM25+lexical method
           ID and records which dense-side provider was used

#### Scenario: Neural hybrid stays config-gated
- **WHEN** the neural text baseline is disabled
- **THEN** BM25+neural RRF is also disabled and no neural embeddings are
           generated

### Requirement: BM25 plus lexical RRF hybrid
The system SHALL provide a hybrid retriever that combines BM25 and lexical
cosine rankings with reciprocal rank fusion and deterministic page-ID
tie-breaking.

#### Scenario: BM25 plus lexical RRF combines rankings
- **WHEN** BM25 and lexical cosine baselines return different top-ranked pages
           for the same query
- **THEN** the BM25+lexical hybrid produces a fused ranking using reciprocal
           rank positions from both baselines

#### Scenario: BM25 plus lexical RRF tie-breaking is stable
- **WHEN** two pages receive the same fused RRF score
- **THEN** their relative order is deterministic and sorted by stable page ID

### Requirement: Text baseline candidate universe disclosure
The text retrieval baseline layer SHALL apply and report the configured
candidate universe for every method.

#### Scenario: Text methods share the same candidate universe
- **WHEN** a text baseline report includes BM25, lexical cosine, neural text,
           or hybrid methods
- **THEN** every enabled method ranks against the same configured candidate page
           universe for that report

#### Scenario: Candidate universe support is method-level visible
- **WHEN** a text baseline report is generated
- **THEN** each method reports ranked page support consistent with the report's
           candidate universe

### Requirement: Text-only neural baseline boundary
The text retrieval baseline layer SHALL NOT read page images, run visual
late-interaction models, emit hard-negative triples, train adapters, create
embedding caches, or evaluate the final test split by default.

#### Scenario: Text baseline execution remains text-only
- **WHEN** the Phase 2.5 text baseline report is generated
- **THEN** it consumes text artifacts and manifests without invoking ColPali,
           ColQwen, image embeddings, hard-negative mining, LoRA/QLoRA
           training, GPU hardware, or final-test query evaluation

## REMOVED Requirements

### Requirement: Deterministic dense-text baseline
**Reason**: The existing local implementation is lexical cosine over local text
tokens, not a neural dense embedding model. Keeping the `dense_text` name makes
diagnostic evidence look stronger than it is.

**Migration**: Rename the local method to `lexical_cosine` or
`local_tfidf_cosine`, update configs, reports, tests, docs, and ledgers, and
use the new config-gated neural text baseline for any future BGE-M3 or
sentence-transformers-style dense method.

### Requirement: Hybrid reciprocal-rank fusion retriever
**Reason**: The current hybrid requirement does not identify whether the dense
side is lexical cosine or a neural text baseline.

**Migration**: Replace it with explicit BM25+lexical RRF and BM25+neural RRF
method contracts so reports disclose which dense-side retrieval method was
used.
