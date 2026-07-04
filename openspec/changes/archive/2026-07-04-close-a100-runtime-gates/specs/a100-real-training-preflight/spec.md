## ADDED Requirements

### Requirement: Phase 5G runtime gate closure evidence
The A100 preflight SHALL record Phase 5G runtime-gate closure evidence from a
fresh A100 observation after any allowed-root dependency setup attempt, without
launching training.

#### Scenario: Dependency gate closes
- **WHEN** the checked A100 runtime can import all required optional modules,
  including `colpali_engine`, from an isolated allowed-root runtime
- **THEN** Phase 5G evidence records dependency readiness and does not report
  `optional_dependency_missing`

#### Scenario: Dependency gate remains blocked
- **WHEN** the checked A100 runtime still cannot import one or more required
  optional modules after the allowed-root setup attempt
- **THEN** Phase 5G evidence records the missing modules, keeps the runtime
  blocked, and reports that training was not launched

### Requirement: Phase 5G allowed-root setup safety
The A100 preflight SHALL keep dependency setup, cache, log, and temporary
outputs under `/mnt/data/minghongsun`.

#### Scenario: Setup writes stay under allowed root
- **WHEN** Phase 5G creates or reuses a Python runtime, package cache, Hugging
  Face cache, or temporary directory
- **THEN** the paths are under `/mnt/data/minghongsun` and committed evidence
  records only sanitized placement status

#### Scenario: Setup would require disallowed writes
- **WHEN** closing a runtime gate would require writing under `/root`, `/tmp`,
  or another user's directory
- **THEN** Phase 5G evidence records a blocked reason and does not perform that
  write

### Requirement: Phase 5G exact model path closure
The A100 preflight SHALL verify only the exact A100-side model path selected
for the phase and SHALL NOT download or infer model weights.

#### Scenario: Exact model path is ready
- **WHEN** `/mnt/data/minghongsun/models/vidore-colqwen2-v1.0-hf` exists on the
  A100 host, is readable by the checked runtime, and has expected model-file
  markers
- **THEN** Phase 5G evidence records redacted model-path readiness and does not
  commit the exact private path

#### Scenario: Exact model path is missing
- **WHEN** `/mnt/data/minghongsun/models/vidore-colqwen2-v1.0-hf` is absent on
  the A100 host
- **THEN** Phase 5G evidence records `missing_local_model_path`, keeps
  `training_launched=false`, and does not download model weights

### Requirement: Phase 5G closure status
The A100 preflight SHALL distinguish gate closure from real-training execution.

#### Scenario: All runtime gates close
- **WHEN** allowed-root setup, dependency importability, CUDA/GPU observation,
  and exact model-path readiness are all true
- **THEN** Phase 5G evidence reports `runtime_ready` while also reporting no
  training, no model download, no adapter checkpoint, no final-test evaluation,
  and no benchmark-improvement claim

#### Scenario: Any runtime gate remains blocked
- **WHEN** at least one runtime gate remains blocked after the closure attempt
- **THEN** Phase 5G evidence reports `blocked` or `needs_user_input` with the
  remaining blocker codes and does not report real-training success
