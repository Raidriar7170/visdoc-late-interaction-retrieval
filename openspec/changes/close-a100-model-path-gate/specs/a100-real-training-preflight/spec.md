## ADDED Requirements

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
