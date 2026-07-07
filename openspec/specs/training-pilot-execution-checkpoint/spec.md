# training-pilot-execution-checkpoint Specification

## Purpose
TBD - created by archiving change run-phase-5c-real-training-pilot. Update Purpose after archive.
## Requirements
### Requirement: Phase 5C pilot attempt gate
The system SHALL attempt a Phase 5C tiny real LoRA / QLoRA pilot only from a
clean `origin/main` branch or dedicated worktree and only when the existing
pilot launcher gates can be truthfully satisfied with local model weights,
CUDA/GPU availability, explicit real-training permission, final-test disabled,
tiny budget, and ignored adapter output.

#### Scenario: Pilot config uses bounded real-training gates
- **WHEN** Phase 5C prepares the local pilot command
- **THEN** the effective config records `allow_real_training=true`,
  `allow_final_test=false`, `max_steps <= 20`, an ignored adapter output
  directory, dev-only inputs, and a run-card boundary of pilot/dev-only/not
  final benchmark

#### Scenario: Private path prerequisites block execution
- **WHEN** the exact private remote repository path or local model path cannot
  be resolved to an existing path in the execution environment
- **THEN** Phase 5C SHALL record a blocked checkpoint instead of guessing,
  downloading, or substituting another model path

### Requirement: Sanitized Phase 5C evidence
The system SHALL commit only sanitized Phase 5C metadata/report evidence and
MUST NOT commit true private model paths, local pilot configs, model weights,
adapter checkpoints, training caches, training logs, or final-test metrics.

#### Scenario: Successful pilot evidence is public-safe
- **WHEN** a tiny pilot actually runs
- **THEN** committed evidence includes a redacted environment check, safety
  check, pilot run-card, sanitized adapter manifest metadata, dev-only eval
  schema or record, human brief, and progress-ledger entry without adapter
  checkpoint files or private paths

#### Scenario: Blocked pilot evidence is public-safe
- **WHEN** the pilot is blocked by a missing prerequisite or scaffold boundary
- **THEN** committed evidence includes the blocked reason, redacted local model
  path summary, max steps, device/GPU summary when available, final-test
  exclusion, and no-claim/no-artifact statements

### Requirement: No benchmark or artifact overclaim
The Phase 5C checkpoint SHALL NOT present pilot loss, blocked status, dry-run
outputs, mock visual results, or dev-only sanity checks as benchmark
improvement, model superiority, final-test performance, or production training
readiness.

#### Scenario: Final test remains unused
- **WHEN** Phase 5C evidence is generated
- **THEN** every report records `final_test_used=false` or an equivalent
  not-run status and contains no final-test metric values

#### Scenario: No improvement claim is added
- **WHEN** Phase 5C evidence and documentation are inspected
- **THEN** they contain no benchmark improvement claim, no README result claim,
  no model superiority claim, and no statement that a blocked or dev-only run
  proves retrieval quality

### Requirement: Existing local validation remains intact
The Phase 5C evidence change SHALL preserve the deterministic MVP pipeline,
hard-negative mining command, Phase 5A dry-run command, and Phase 5B blocked
example command as local validation surfaces.

#### Scenario: Required validation commands remain runnable
- **WHEN** the Phase 5C branch is validated locally
- **THEN** the MVP command, hard-negative mining command, Phase 5A dry-run
  command, Phase 5B example pilot command, py_compile, pyproject parse, pytest,
  Ruff, mypy, OpenSpec strict validation, and `git diff --check` complete or
  report a truthful blocking reason
