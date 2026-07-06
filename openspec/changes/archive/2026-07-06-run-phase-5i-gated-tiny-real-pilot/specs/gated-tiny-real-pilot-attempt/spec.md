## ADDED Requirements

### Requirement: Phase 5I gated tiny real-pilot launch
The system SHALL attempt the Phase 5I tiny real LoRA / QLoRA pilot only from a
clean `origin/main` branch or dedicated worktree and only when the existing
guarded launcher truthfully satisfies every real-training gate.

#### Scenario: Phase 5I local config uses bounded real-training gates
- **WHEN** Phase 5I prepares the untracked local pilot config
- **THEN** the effective config records `allow_real_training=true`,
  `allow_final_test=false`, `VISDOC_ENABLE_REAL_TRAINING=1`,
  `max_steps <= 20`, `sample_limit <= 8`, an ignored adapter output directory,
  dev-only inputs, and a pilot/dev-only/not-final-benchmark run-card boundary

#### Scenario: Missing gate blocks the pilot instead of guessing
- **WHEN** the exact A100-readable model path, CUDA/GPU, optional dependency,
  explicit environment flag, or ignored adapter output gate is not satisfied
- **THEN** Phase 5I SHALL record a blocked checkpoint instead of downloading a
  model, guessing another path, widening the budget, or claiming success

### Requirement: Phase-specific public pilot evidence
The system SHALL allow the guarded pilot launcher to emit phase-specific public
metadata for schemas, titles, run-card names, and progress-ledger sections
without changing Phase 5D default behavior.

#### Scenario: Default Phase 5D behavior remains stable
- **WHEN** the committed example config is used
- **THEN** the launcher still emits the existing Phase 5D schema IDs,
  run-card names, and `training_pilot_phase_5d_status` progress-ledger section

#### Scenario: Phase 5I public metadata is emitted from the local config
- **WHEN** the untracked Phase 5I local config provides phase metadata and
  Phase 5I output file names
- **THEN** committed evidence uses Phase 5I schema IDs, Phase 5I run-card
  titles, the requested Phase 5I artifact file names, and a Phase 5I
  progress-ledger section

### Requirement: Sanitized Phase 5I pilot evidence
The system SHALL commit only sanitized Phase 5I evidence and MUST NOT commit
the true private model path, local pilot config contents, model weights,
adapter checkpoints, training caches, or final-test metrics.

#### Scenario: Successful pilot evidence is public-safe
- **WHEN** the tiny pilot runs successfully
- **THEN** committed evidence includes a sanitized environment check, safety
  check, pilot run-card, sanitized adapter manifest metadata, dev-only eval
  JSON, Human Brief, and progress-ledger entry without exact private model
  paths, local config contents, adapter files, or weights

#### Scenario: Blocked pilot evidence is public-safe
- **WHEN** the tiny pilot is blocked by a real prerequisite or guarded backend
  outcome
- **THEN** committed evidence includes the blocked reason, redacted model-path
  summary, max steps, sample limit, device summary when available, and
  no-claim/no-artifact statements without faking training success

### Requirement: No final-test or benchmark overclaim
Phase 5I SHALL NOT present pilot loss, dev-only sanity output, or blocked
status as benchmark improvement, final-test performance, or production
training success.

#### Scenario: Final test remains unused
- **WHEN** Phase 5I evidence is generated
- **THEN** every Phase 5I report records `final_test_used=false` or an
  equivalent not-run status and contains no final-test metric values

#### Scenario: No benchmark improvement claim is added
- **WHEN** Phase 5I reports, ledger entries, and Human Brief are inspected
- **THEN** they contain no benchmark improvement claim, no README result claim,
  no model superiority claim, and no statement that pilot loss or dev-only
  sanity proves retrieval quality

### Requirement: Existing validation surfaces remain intact
The Phase 5I change SHALL preserve the existing MVP, hard-negative mining, dry
run, and blocked example pilot validation surfaces while adding the Phase 5I
reporting behavior.

#### Scenario: Required validation commands remain runnable
- **WHEN** the Phase 5I branch is validated
- **THEN** the MVP command, hard-negative mining command, dry-run command,
  blocked example pilot command, py_compile, pyproject parse, pytest, Ruff,
  mypy, OpenSpec strict validation, and `git diff --check` complete or report a
  truthful blocking reason without requiring model download or final-test data
