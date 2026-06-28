## ADDED Requirements

### Requirement: Phase 0 repository skeleton
The change SHALL create a minimal Python repository skeleton for VisDoc-Retrieve without implementing retrieval, data, model, training, or evaluation logic.

#### Scenario: Skeleton surfaces exist
- **WHEN** Phase 0 is applied
- **THEN** the repository contains `README.md`, `AGENTS.md`, `pyproject.toml`, `src/visdoc_retrieve/`, `tests/`, `configs/`, `reports/`, and `data/README.md`

### Requirement: Algorithmic project positioning
The README SHALL position VisDoc-Retrieve as a page-level multimodal document retrieval and ranking project focused on OCR/text baselines, visual late interaction, hard-negative mining, and future LoRA adaptation.

#### Scenario: README first screen preserves project focus
- **WHEN** a reader opens the README after Phase 0 is applied
- **THEN** the first screen emphasizes visual document retrieval and SHALL NOT lead with chatbot UI, generic RAG orchestration, Agent behavior, browser automation, citation safety, production RAG deployment, or QA generation

### Requirement: No unsupported result claims
The README SHALL explicitly state that no final benchmark results exist yet and MUST NOT claim retrieval improvement, model superiority, or frozen-test performance.

#### Scenario: README has no premature benchmark claims
- **WHEN** Phase 0 acceptance checks review README content
- **THEN** the README contains a no-final-results statement and contains no numeric improvement claims or final result table

### Requirement: Bounded progress ledger
The change SHALL initialize a bounded project progress ledger under `reports/` with Phase 0 project state and no unbounded historical log.

#### Scenario: Progress ledger starts in bootstrap state
- **WHEN** Phase 0 is applied
- **THEN** the progress ledger records `current_phase: 0`, `status: BOOTSTRAPPED` or an equivalent Phase 0 status, and records that data, visual retriever, training, and final test outputs are not yet available

### Requirement: Future-phase work remains excluded
The change SHALL NOT introduce data generation, page rendering, OCR extraction, retrieval models, retrieval metrics, ColPali/ColQwen inference, hard-negative mining, training scripts, adapter checkpoints, or benchmark reports.

#### Scenario: Phase 0 stays implementation-light
- **WHEN** Phase 0 is reviewed
- **THEN** the changed files are limited to OpenSpec artifacts, project metadata, documentation, placeholder directories, minimal package initialization, and smoke validation tests
