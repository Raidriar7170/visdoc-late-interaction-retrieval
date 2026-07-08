# project-milestone-narrative Specification

## Purpose
Keep the repository homepage, evidence index, and milestone brief aligned with
the current project state while preserving no-final-test and no-benchmark-claim
boundaries.
## Requirements
### Requirement: Current project milestone narrative
The repository SHALL publish a current-status narrative that reflects the
merged Phase 5K state without adding benchmark or final-test claims.

#### Scenario: README reflects current milestone
- **WHEN** a reader opens `README.md`
- **THEN** the current status SHALL mention the diagnostic MVP pipeline, text
  baselines, explicit candidate universe, mock visual late-interaction scaffold,
  optional visual backend or A100 gates, hard-negative mining, training
  readiness and safety gates, reviewed tiny LoRA runner proof, and dev-only
  pilot evaluation harness
- **AND** it SHALL state that final benchmark and final test have not been run
- **AND** it SHALL state that no benchmark improvement claim, model weights, or
  adapter checkpoints are committed

### Requirement: Evidence index
The repository SHALL provide an evidence index that maps major project
milestones to authoritative reports, Human Briefs, and OpenSpec archive
locations.

#### Scenario: Evidence paths are discoverable
- **WHEN** a reviewer inspects the evidence index
- **THEN** it SHALL include MVP reports, hard-negative reports, training
  readiness reports, A100 gate reports, Phase 5J tiny runner proof reports,
  Phase 5K dev-only evaluation reports, and relevant OpenSpec archive paths
- **AND** it SHALL preserve no-final-test and no-benchmark-claim boundaries

### Requirement: Recruiter-facing milestone brief
The repository SHALL provide a recruiter-facing milestone brief that explains
current project completion and limits in plain language.

#### Scenario: Milestone brief avoids overclaiming
- **WHEN** the milestone brief is read
- **THEN** it SHALL explain what is demonstrable, what is not a final result,
  why `max_steps=1` / `sample_limit=1` is not a benchmark, why dev-only
  evaluation is not final test, and what the recommended next step is

### Requirement: Unicode-control hygiene
The Phase 6A documentation checkpoint SHALL scan Markdown, YAML, and JSON files
for bidi Unicode control characters.

#### Scenario: Bidi scan is clean or explicitly handled
- **WHEN** Phase 6A validation runs
- **THEN** the Unicode-control scan SHALL report no bidi control characters or
  document any false positive without damaging Chinese text

### Requirement: Final presentation package
The repository SHALL provide final presentation materials after the Phase 6D
one-time frozen final comparison while preserving the final benchmark and
no-retune boundaries.

#### Scenario: README reflects final status
- **WHEN** a reader opens `README.md` after Phase 7A
- **THEN** the README SHALL state that Phase 6D completed a one-time frozen
  final comparison
- **AND** it SHALL state that the no-retune pledge is active
- **AND** it SHALL state that the final claim checklist does not support a clear
  benchmark improvement claim
- **AND** it SHALL identify systems that ran and systems that were
  `not_available`
- **AND** it SHALL label `mock_visual` as a deterministic scaffold, not real
  visual-model performance
- **AND** it SHALL label the tiny A100 runner proof as pipeline evidence, not
  benchmark performance

#### Scenario: Presentation docs avoid unsupported claims
- **WHEN** a reviewer reads the project card, resume bullets, or interview
  talking points
- **THEN** those files SHALL avoid unsupported benchmark-improvement wording
- **AND** they SHALL not present tiny LoRA runner proof as formal training gain
- **AND** they SHALL not present `mock_visual` as real visual model performance
- **AND** they SHALL link to the final evidence paths that support the claims

#### Scenario: Final evidence remains immutable
- **WHEN** Phase 7A is committed
- **THEN** `reports/final-comparison/final-metrics.json` SHALL remain unchanged
- **AND** `reports/final-comparison/final-rankings.csv` SHALL remain unchanged
- **AND** `reports/final-comparison/final-comparison-run-manifest.json` SHALL
  remain unchanged
- **AND** retrieval behavior and metric definitions SHALL remain unchanged

#### Scenario: Reviewer-facing text hygiene is clean
- **WHEN** Phase 7A validation runs
- **THEN** Markdown, YAML, JSON, and TOML reviewer-facing files SHALL contain no
  hidden Unicode/control characters other than allowed newlines, carriage
  returns, and tabs
- **AND** normal Chinese text SHALL be preserved
