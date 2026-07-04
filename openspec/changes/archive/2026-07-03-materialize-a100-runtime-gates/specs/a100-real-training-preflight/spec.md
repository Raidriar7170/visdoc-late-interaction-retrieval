## ADDED Requirements

### Requirement: Phase 5F runtime gate evidence
The A100 preflight SHALL materialize Phase 5F runtime-gate evidence from
structured observations of the checked remote environment, without executing
package installation or training from the evidence writer.

#### Scenario: Runtime dependency gate is blocked
- **WHEN** a required optional runtime dependency such as `colpali_engine` is
  not importable in the checked environment
- **THEN** Phase 5F evidence records `optional_dependency_missing`, keeps the
  runtime gate blocked, and reports that training was not launched

#### Scenario: Runtime dependency gate is ready
- **WHEN** required optional runtime dependencies are importable in an isolated
  allowed-root environment
- **THEN** Phase 5F evidence records dependency readiness and does not report a
  dependency blocker

### Requirement: Phase 5F model path gate evidence
The A100 preflight SHALL require an exact A100-readable local model path and
SHALL commit only redacted model-path readiness evidence.

#### Scenario: Exact model path is not provided
- **WHEN** no exact local ColPali / ColQwen model path is provided
- **THEN** Phase 5F evidence records `needs_user_model_path`, marks
  `user_input_required=true`, and does not infer readiness from unrelated
  directories

#### Scenario: Provided model path is missing
- **WHEN** an exact local model path is provided but does not exist on the A100
  host
- **THEN** Phase 5F evidence records `missing_local_model_path` without
  committing the exact private path

#### Scenario: Provided model path is not A100-readable
- **WHEN** a provided path is local to another machine or is not confirmed
  readable from the A100 runtime
- **THEN** Phase 5F evidence records `local_model_path_not_a100_readable` and
  does not mark the model-path gate ready

#### Scenario: Provided model path has expected shape
- **WHEN** an exact local model path exists and the structured observation says
  expected model-file markers are present
- **THEN** Phase 5F evidence records only redacted path location and model-shape
  readiness

### Requirement: Phase 5F runtime-ready status
The A100 preflight SHALL distinguish runtime-gate readiness from real-training
execution success.

#### Scenario: All runtime gates are ready
- **WHEN** allowed-root runtime placement, dependency importability, CUDA,
  safe idle-GPU observation, and exact model-path checks are all ready
- **THEN** Phase 5F evidence reports `runtime_ready` and still reports no
  training, model download, adapter checkpoint, final-test evaluation, or
  benchmark-improvement claim

#### Scenario: User input is the only blocker
- **WHEN** the only remaining blocker is an exact user-provided model path
- **THEN** Phase 5F evidence reports `needs_user_input` rather than
  `runtime_ready`

### Requirement: Phase 5F public-safe evidence
The A100 preflight SHALL write Phase 5F JSON, safety, run-card, progress-ledger,
and Human Brief evidence without private operational details.

#### Scenario: Phase 5F evidence is committed
- **WHEN** Phase 5F evidence is added to the repository
- **THEN** it excludes host IPs, SSH details, process IDs, exact private model
  paths, secrets, model weights, adapters, checkpoints, caches, final-test
  metrics, and benchmark claims
