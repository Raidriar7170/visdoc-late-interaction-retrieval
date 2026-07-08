# release-readiness Specification

## Purpose
TBD - created by archiving change prepare-v0-1-final-release. Update Purpose after archive.
## Requirements
### Requirement: Release preparation evidence
The repository SHALL provide reviewable release-preparation evidence before any
final tag or GitHub Release is created.

#### Scenario: Release notes preserve benchmark boundaries
- **WHEN** a reviewer reads the `v0.1.0` release notes
- **THEN** the notes SHALL state that Phase 6D completed a one-time frozen final
  comparison
- **AND** the notes SHALL state that the final claim checklist records
  `no_clear_improvement_claim`
- **AND** the notes SHALL not claim benchmark improvement, model superiority, or
  real visual-model performance from `mock_visual`
- **AND** the notes SHALL state that `tiny_lora_adapter` and
  `zero_shot_visual_backend` were `not_available`

#### Scenario: Tag execution remains explicitly gated
- **WHEN** the release-preparation PR is merged
- **THEN** no tag SHALL be created by that PR
- **AND** no GitHub Release SHALL be published by that PR
- **AND** any documented tag or release commands SHALL be marked as manual
  commands that require explicit user confirmation

#### Scenario: Release readiness report is machine-readable
- **WHEN** the release-preparation phase completes
- **THEN** it SHALL include a machine-readable readiness report
- **AND** the report SHALL record open PR status, active OpenSpec status,
  planned release name, planned tag target policy, validation results, and
  boundary confirmations

#### Scenario: Final evidence remains immutable
- **WHEN** release-preparation files are committed
- **THEN** final metrics, final rankings, final run manifest, final claim
  checklist, retrieval behavior, and metric definitions SHALL remain unchanged
