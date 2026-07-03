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
