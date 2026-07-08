## ADDED Requirements

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
