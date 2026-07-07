# final-comparison-protocol Specification

## Purpose
TBD - created by archiving change freeze-final-comparison-protocol. Update Purpose after archive.
## Requirements
### Requirement: Final-test access gate
The system SHALL require an explicit frozen protocol checkpoint before any
final-test split files are read for evaluation.

#### Scenario: Default validation does not read final test
- **WHEN** local validation runs for Phase 6B
- **THEN** it SHALL NOT read final-test files or generate final-test metrics
- **AND** it SHALL record final-test status as `not_run`

#### Scenario: Final-test execution requires a later change
- **WHEN** a future phase wants to evaluate the final test
- **THEN** it SHALL require a new OpenSpec change that names the frozen
  protocol version, authorized inputs, candidate universe, model or adapter
  source, and claim-review checklist

### Requirement: Final comparison schema
The system SHALL define a comparison schema that separates diagnostic,
dev-only, longer-dev, and final benchmark rows.

#### Scenario: Schema preserves unavailable metrics
- **WHEN** a method has not been run under the required protocol
- **THEN** its row SHALL use `not_run`, `not_available`, or `blocked` status
  instead of fabricated metric values

#### Scenario: Schema includes boundary metadata
- **WHEN** a comparison row is recorded
- **THEN** it SHALL include split scope, candidate universe, artifact source,
  adapter status, final-test usage, benchmark-claim status, and evidence path

### Requirement: Benchmark claim checklist
The system SHALL provide a public-safe checklist that blocks benchmark
improvement claims unless the frozen protocol is satisfied.

#### Scenario: Claim is blocked before final protocol completion
- **WHEN** final-test authorization, final comparison metrics, artifact hygiene,
  or reviewer approval is missing
- **THEN** the claim checklist SHALL record the benchmark claim as blocked

#### Scenario: Dev-only and tiny-runner evidence are labeled correctly
- **WHEN** dev-only harness evidence or `max_steps=1` / `sample_limit=1` tiny
  runner proof is referenced
- **THEN** the checklist SHALL label it as sanity or pipeline evidence, not
  final benchmark evidence

### Requirement: Artifact hygiene boundary
The final-comparison protocol SHALL keep public evidence free of committed
model weights, adapter checkpoints, training caches, private config, and exact
private model paths.

#### Scenario: Protocol evidence is public-safe
- **WHEN** Phase 6B protocol evidence is inspected
- **THEN** it SHALL state that no model weights, adapter checkpoints, cache
  artifacts, private configs, exact private model paths, final-test metrics, or
  benchmark improvement claims are committed

### Requirement: Phase 6B validation surface
The Phase 6B protocol freeze SHALL preserve existing local validation behavior
without requiring A100 access, network access, model downloads, training, or
final-test data.

#### Scenario: Local validation remains CPU/documentation-only
- **WHEN** Phase 6B validation is run locally
- **THEN** MVP, hard-negative mining, LoRA dry-run, blocked pilot gate,
  py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation,
  and `git diff --check` SHALL pass without launching training or reading final
  test data
