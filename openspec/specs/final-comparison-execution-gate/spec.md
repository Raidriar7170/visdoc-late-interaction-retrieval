# final-comparison-execution-gate Specification

## Purpose
TBD - created by archiving change add-final-comparison-execution-gate-dry-run. Update Purpose after archive.
## Requirements
### Requirement: Phase 6C final-comparison dry-run gate
The system SHALL provide a Phase 6C execution gate that validates frozen final
comparison readiness without reading final-test files or running the final
comparison.

#### Scenario: Dry-run gate reads only protocol and public evidence
- **WHEN** the Phase 6C dry-run gate runs with checked-in defaults
- **THEN** it SHALL read the frozen Phase 6B protocol status, comparison
  schema, claim checklist, public evidence reports, and OpenSpec active-state
  output
- **AND** it SHALL NOT read final-test qrels, final-test labels, final-test
  metrics, private configs, model weights, adapter checkpoints, or training
  caches

#### Scenario: Active OpenSpec state is recorded
- **WHEN** active OpenSpec changes are present
- **THEN** the gate SHALL record their names
- **AND** it SHALL pass only when the active state is empty after merge or
  contains the Phase 6C change as the sole active development change

### Requirement: Required artifact readiness checks
The Phase 6C gate SHALL check required artifacts before any final comparison is
allowed.

#### Scenario: Required artifacts are classified honestly
- **WHEN** a required artifact is missing
- **THEN** the gate SHALL record that artifact as `missing` or `blocked`
  instead of fabricating readiness, metrics, or final-comparison results

#### Scenario: Frozen inputs are explicitly checked
- **WHEN** required artifacts are present
- **THEN** the gate SHALL check protocol status, comparison schema, claim
  checklist, candidate universe, split policy, metric definitions, MVP
  evidence, hard-negative evidence, training-readiness evidence, training
  pilot evidence, dev-only harness evidence, final-test guard, output path
  safety, and no-tuning-after-final documentation

### Requirement: Dry-run reports remain non-final
The Phase 6C gate SHALL emit planned-run and readiness reports without running
the final comparison or adding benchmark claims.

#### Scenario: Dry-run outputs do not contain final metrics
- **WHEN** Phase 6C evidence is generated
- **THEN** it SHALL state `final_test_read=false`,
  `final_comparison_execution=not_executed`, and
  `benchmark_improvement_claim=false`
- **AND** planned final rows SHALL contain expected artifact paths and
  readiness statuses, not final-test metric values

#### Scenario: Claim checklist blocks pre-final claims
- **WHEN** the final comparison has not been authorized and executed
- **THEN** the Phase 6C claim checklist SHALL keep benchmark claims blocked
  and list final-test authorization, final-test execution, final metrics, and
  reviewer approval as missing prerequisites

### Requirement: Existing local validation remains intact
The Phase 6C change SHALL preserve existing MVP, hard-negative mining,
training dry-run, and blocked pilot validation behavior.

#### Scenario: Existing commands still run locally
- **WHEN** Phase 6C is validated locally
- **THEN** MVP, hard-negative mining, LoRA dry-run, blocked pilot gate,
  py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation,
  and `git diff --check` SHALL pass without A100 access, SSH, GPU, network,
  model downloads, final-test data, real final comparison, or benchmark
  metrics

### Requirement: One-time frozen final comparison execution
The system SHALL execute the Phase 6D final comparison exactly once under the
frozen Phase 6B protocol after Phase 6C readiness has been archived.

#### Scenario: Final run records immutable provenance
- **WHEN** the final comparison command runs
- **THEN** it SHALL write a run manifest containing the git commit, run id,
  timestamp, protocol version, protocol hash, candidate-universe hash, split
  policy, metric-definition hash, final-test qrels hash, config hash, and
  no-retune pledge status
- **AND** it SHALL record that the final-test split was read by the authorized
  Phase 6D command

#### Scenario: Final run cannot be repeated silently
- **WHEN** default final comparison outputs already exist
- **THEN** the command SHALL fail unless an explicit override is provided for
  non-committed test use

### Requirement: Final benchmark rows are honest
The system SHALL report only systems that were actually run or explicitly mark
systems as unavailable.

#### Scenario: Available frozen systems get final metrics
- **WHEN** deterministic frozen systems run on the final split
- **THEN** final metrics SHALL include Recall@1, Recall@5, MRR, NDCG@10,
  support counts, and subset metrics

#### Scenario: Missing systems are not fabricated
- **WHEN** an optional visual backend, adapter, cascade, or other system lacks
  a frozen artifact
- **THEN** its row SHALL use `not_available` or `not_run` status and SHALL NOT
  include fabricated metric values

### Requirement: Final claim checklist remains conservative
The system SHALL block unsupported benchmark-improvement claims after the final
run.

#### Scenario: Mixed or unsupported outcome is reported honestly
- **WHEN** final metrics do not support a clear improvement claim
- **THEN** the final report and claim checklist SHALL state that no clear
  improvement claim is supported
- **AND** dev-only or tiny-runner evidence SHALL remain labeled as non-final
  pipeline evidence
