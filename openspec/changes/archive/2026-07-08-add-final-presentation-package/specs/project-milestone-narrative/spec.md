## ADDED Requirements

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
