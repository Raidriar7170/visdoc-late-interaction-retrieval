## ADDED Requirements

### Requirement: Reviewed tiny LoRA backend runner
The system SHALL provide a repo-owned reviewed backend runner for the A100
tiny LoRA pilot when the existing launcher gates pass and
`backend_dependency=colpali_engine` is importable without a project-specific
third-party runner hook.

#### Scenario: Runner remains behind existing gates
- **WHEN** the guarded pilot command is executed
- **THEN** the runner SHALL only be reachable after `allow_real_training=true`,
  `allow_final_test=false`, `VISDOC_ENABLE_REAL_TRAINING=1`,
  `local_files_only=true`, CUDA availability, local model path existence,
  hard-negative artifact checks, tiny budget caps, and ignored adapter output
  checks pass

#### Scenario: Third-party runner hook still takes precedence
- **WHEN** the selected backend dependency exposes a callable
  `run_visdoc_lora_pilot`
- **THEN** the system SHALL continue to use that hook and normalize its result
  through the existing safety sanitizer

#### Scenario: Repo-owned ColQwen2 runner is used when hook is absent
- **WHEN** `backend_dependency=colpali_engine` is importable but does not expose
  a callable `run_visdoc_lora_pilot`
- **THEN** the system SHALL use the reviewed repo-owned tiny runner instead of
  returning `backend_training_step_unavailable` solely because the hook is
  absent

### Requirement: Tiny optimizer-backed pilot result
The reviewed runner SHALL report `pilot_run` only after a real
optimizer-backed training step is performed within the configured tiny budget.

#### Scenario: Successful tiny optimizer step
- **WHEN** the reviewed runner loads the local model and processor, wraps the
  model with LoRA, processes capped training samples, computes a scalar loss,
  runs backward propagation, and performs at least one optimizer step
- **THEN** it SHALL return `status=pilot_run`, `training_executed=true`,
  `effective_training_sample_count` within the configured sample cap,
  `final_test_used=false`, no metric or improvement fields, and adapter
  metadata that matches the configured ignored output directory

#### Scenario: No optimizer step means no pilot success
- **WHEN** model loading, processor encoding, LoRA wrapping, loss computation,
  backward propagation, optimizer stepping, or optional adapter saving cannot
  safely complete
- **THEN** the runner SHALL return `status=blocked`, `training_executed=false`,
  `final_test_used=false`, no adapter checkpoint path, and an exact blocked
  code describing the failed stage

### Requirement: Phase 5J public-safe evidence
The system SHALL record Phase 5J runner evidence without committing private
paths, model weights, adapter checkpoints, caches, final-test metrics, or
benchmark improvement claims.

#### Scenario: Successful runner evidence is sanitized
- **WHEN** Phase 5J records a successful tiny runner pilot
- **THEN** committed evidence SHALL include sanitized environment, safety,
  run-card, adapter manifest, dev-eval schema, progress-ledger, and Human Brief
  artifacts that state final test was unused and no benchmark improvement is
  claimed

#### Scenario: Blocked runner evidence is sanitized
- **WHEN** Phase 5J records a blocked tiny runner attempt
- **THEN** committed evidence SHALL include the exact blocked reason and
  bounded command metadata without the exact private model path, local config
  contents, adapter files, weights, caches, final-test metrics, or benchmark
  improvement claims

### Requirement: Existing validation surfaces remain intact
The Phase 5J change SHALL preserve existing Phase 5D and Phase 5I launcher,
blocked example, dry-run, MVP, and hard-negative validation behavior while
adding the reviewed tiny runner path.

#### Scenario: Local validation does not require A100 resources
- **WHEN** focused unit tests for Phase 5J run locally
- **THEN** they SHALL use fake modules, models, processors, tensors, and
  optimizers where needed so validation can verify the runner contract without
  CUDA, local model weights, downloads, or final-test data

#### Scenario: Full validation keeps no-claim boundaries
- **WHEN** the Phase 5J branch is validated
- **THEN** OpenSpec strict validation, focused tests, lint/diff checks, and
  boundary scans SHALL pass or report a truthful blocker without requiring
  model download, final-test data, or benchmark metrics
