# a100-real-training-preflight Specification

## Purpose
Defines the Phase 5E A100 setup/preflight contract for allowed-root remote
preparation, GPU and dependency checks, exact local model-path gating, and
public-safe evidence before any real-training pilot is launched.
## Requirements
### Requirement: Allowed-root remote setup
The Phase 5E preflight SHALL create or verify remote project, environment,
cache, log, and temporary paths only under `/mnt/data/minghongsun`.

#### Scenario: Remote checkout uses allowed root
- **WHEN** the preflight prepares or verifies the remote VisDoc repository
- **THEN** the repository path is under `/mnt/data/minghongsun` and no project
  file is written under `/root`, `/tmp`, or another user's directory

#### Scenario: Disallowed write target blocks setup
- **WHEN** a required setup step would write outside `/mnt/data/minghongsun`
- **THEN** the preflight records a blocked reason and does not perform that
  write

### Requirement: Remote repository checkout evidence
The Phase 5E preflight SHALL record whether a remote VisDoc checkout exists at
the expected allowed-root path and whether it resolves to the intended branch
or commit, without committing remote secrets.

#### Scenario: Checkout is present
- **WHEN** the remote repository exists and Git metadata can be inspected
- **THEN** committed evidence records a sanitized checkout status, branch or
  commit summary, and clean/dirty state

#### Scenario: Checkout is unavailable
- **WHEN** the remote repository cannot be created or inspected
- **THEN** committed evidence records a blocked reason without embedding SSH
  configuration, private network addresses, credentials, or raw remote logs

### Requirement: GPU and dependency preflight
The Phase 5E preflight SHALL check GPU/CUDA availability and optional
real-training dependency importability without launching training.

#### Scenario: CUDA devices are visible
- **WHEN** the remote Python runtime can import torch and query CUDA
- **THEN** evidence records CUDA availability, device count, coarse GPU model
  summary, and safe idle-GPU candidates without process IDs

#### Scenario: Optional dependency is missing
- **WHEN** a Phase 5D backend dependency such as `colpali_engine` is not
  importable
- **THEN** evidence records `optional_dependency_missing` and keeps the real
  pilot blocked

### Requirement: Local model path preflight
The Phase 5E preflight SHALL require an exact user-provided local model path
before declaring the remote environment preflight-ready.

#### Scenario: Model path is unknown
- **WHEN** no exact local ColPali / ColQwen model path is available
- **THEN** evidence records `needs_user_model_path` or an equivalent blocked
  reason and does not infer readiness from unrelated model directories

#### Scenario: Model path exists
- **WHEN** an exact local model path is provided and exists on the remote host
- **THEN** evidence records only a redacted path summary and existence status,
  not the exact private path

### Requirement: No training or model artifact side effects
The Phase 5E preflight SHALL NOT run real training, download models, read final
test data, create adapter checkpoints, or claim retrieval improvement.

#### Scenario: Preflight completes
- **WHEN** the Phase 5E preflight finishes with ready, blocked, or
  needs-user-input status
- **THEN** committed evidence states that training was not launched, model
  download was not executed, final test was not used, no adapter/checkpoint was
  created, and no benchmark-improvement claim was made

### Requirement: Public-safe Phase 5E evidence
The Phase 5E preflight SHALL write public-safe evidence and a concise Chinese
Human Brief that summarize readiness and remaining blockers.

#### Scenario: Evidence is committed
- **WHEN** Phase 5E evidence is added to the repository
- **THEN** it includes sanitized status, checked commands at a high level,
  blocker codes, key artifact links, validation commands, and the recommended
  next step without host IPs, SSH details, process IDs, secrets, model weights,
  adapters, checkpoints, or exact private model paths

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

### Requirement: Phase 5H exact model-path marker closure
The A100 preflight SHALL record Phase 5H model-path gate closure evidence from
the exact A100-side model directory using static filesystem markers only.

#### Scenario: Exact model path markers are ready
- **WHEN** the exact model directory exists under the allowed A100 root, is
  readable by the checked runtime, and has config, weight, and
  processor-or-tokenizer markers
- **THEN** Phase 5H evidence records the model-path gate as closed and reports
  redacted model-path readiness without committing the exact private path

#### Scenario: Exact model path is missing
- **WHEN** the exact model directory is expected but absent on the A100 host
- **THEN** Phase 5H evidence records `missing_local_model_path`, marks
  `user_input_required=true`, keeps the runtime blocked, and does not download
  model weights

#### Scenario: Exact model path markers are incomplete
- **WHEN** the exact model directory exists but required static model markers
  are incomplete
- **THEN** Phase 5H evidence records `model_shape_markers_missing`, keeps the
  model-path gate blocked, and does not load the model

#### Scenario: Exact model path is outside the allowed root
- **WHEN** a provided model path is outside `/mnt/data/minghongsun`
- **THEN** Phase 5H evidence records `local_model_path_outside_allowed_root`
  and does not mark the model-path gate ready

### Requirement: Phase 5H runtime-ready but not execution-ready boundary
The A100 preflight SHALL distinguish Phase 5H runtime readiness from
real-training execution or benchmark success.
The `runtime_ready` outcome SHALL mean the runtime can proceed only to a
separately gated pilot attempt, not that training succeeded.

#### Scenario: All pre-training gates are closed
- **WHEN** inherited allowed-root placement, dependency importability,
  CUDA/GPU observation, and exact model-path marker gates are all ready
- **THEN** Phase 5H evidence reports `runtime_ready` while also reporting no
  training, no model loading, no model download, no adapter checkpoint, no
  final-test evaluation, and no benchmark-improvement claim

#### Scenario: Any pre-training gate remains blocked
- **WHEN** at least one inherited runtime gate or model-path marker gate remains
  blocked
- **THEN** Phase 5H evidence reports `blocked` or `needs_user_input` with the
  remaining blocker codes and does not report real-training success

### Requirement: Phase 5H public-safe evidence package
The A100 preflight SHALL write Phase 5H JSON, safety, run-card,
progress-ledger, and Human Brief evidence without private operational details
or model artifacts.

#### Scenario: Phase 5H evidence is committed
- **WHEN** Phase 5H evidence is added to the repository
- **THEN** it excludes host IPs, SSH details, process IDs, exact private model
  paths, secrets, model weights, adapters, checkpoints, caches, final-test
  metrics, benchmark claims, model-download claims, and real-training execution
  claims
