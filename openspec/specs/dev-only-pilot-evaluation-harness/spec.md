# dev-only-pilot-evaluation-harness Specification

## Purpose
Define the dev-only Phase 5K pilot evaluation harness contract, including
public-safe evidence, missing-adapter handling, comparison-schema boundaries,
and validation requirements that keep pilot sanity separate from final
benchmark claims.
## Requirements
### Requirement: Phase 5K dev-only evaluation harness
The system SHALL provide a reproducible Phase 5K harness that reads sanitized
pilot evidence and dev split artifacts only, without requiring A100 access,
network access, model downloads, final-test data, or committed adapter
checkpoints.

#### Scenario: Harness reads dev split only
- **WHEN** the Phase 5K harness runs with its checked-in config
- **THEN** it SHALL read dev split hard-negative artifacts and sanitized pilot
  manifests
- **AND** it SHALL NOT read final-test files or paths

#### Scenario: Missing adapter does not fabricate metrics
- **WHEN** the sanitized pilot manifest references an ignored or unavailable
  adapter checkpoint
- **THEN** the harness SHALL record `tiny_pilot_adapter.status=not_available`
  and keep metric values null instead of fabricating adapter metrics

### Requirement: Public-safe Phase 5K evidence
The system SHALL emit Phase 5K evidence that is public-safe and explicitly
scoped to dev-only pilot sanity.

#### Scenario: Evidence preserves no-claim boundaries
- **WHEN** Phase 5K evidence is generated
- **THEN** it SHALL state `final_test_used=false`,
  `benchmark_improvement_claim=false`, and
  `pilot_loss_reported_as_model_improvement=false`
- **AND** it SHALL not contain exact private model paths, private local config
  contents, model weights, adapter checkpoints, or training caches

#### Scenario: Run-card boundary wording is explicit
- **WHEN** the run-card or Human Brief is inspected
- **THEN** it SHALL say the phase is a pilot/dev-only/not-final-benchmark
  harness checkpoint and SHALL NOT present dev-only sanity as a final
  benchmark

### Requirement: Comparison schema remains schema-only when evidence is absent
The system SHALL generate a comparison schema that can represent text
baseline, optional zero-shot visual baseline, and tiny pilot adapter status
without claiming benchmark improvement.

#### Scenario: Optional entries remain honest
- **WHEN** a baseline report or adapter artifact is unavailable
- **THEN** the comparison schema SHALL record `not_available` or `schema_only`
  for that entry instead of inventing metrics

#### Scenario: Tiny pilot budget is bounded
- **WHEN** Phase 5K records pilot gate metadata
- **THEN** `max_steps` SHALL be no greater than 20 and `sample_limit` SHALL be
  no greater than 8

### Requirement: Existing validation surfaces remain intact
The Phase 5K change SHALL preserve existing MVP, hard-negative mining, dry-run,
and blocked pilot gate validation behavior.

#### Scenario: Existing commands still run
- **WHEN** Phase 5K is validated locally
- **THEN** MVP, hard-negative mining, LoRA dry-run, blocked pilot gate,
  py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation,
  and `git diff --check` SHALL pass without requiring A100 access, model
  download, final-test data, or benchmark metrics
