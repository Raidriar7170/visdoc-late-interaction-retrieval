## ADDED Requirements

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
