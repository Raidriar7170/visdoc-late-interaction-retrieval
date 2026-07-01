## ADDED Requirements

### Requirement: Phase 5D real backend gates
The system SHALL attempt a real LoRA / QLoRA training pilot only after every
Phase 5D gate passes: `allow_real_training=true`, `allow_final_test=false`,
`VISDOC_ENABLE_REAL_TRAINING=1`, an existing local model path, CUDA available,
optional training dependencies available, `max_steps <= 20`,
`sample_limit <= 8`, an ignored adapter output directory, and run-card wording
that marks the run as pilot/dev-only/not final benchmark.

#### Scenario: Default config blocks without training
- **WHEN** the committed local example config is run in default validation
- **THEN** the command exits with blocked evidence and does not execute real
  training, require CUDA, require optional ML dependencies, download models, or
  write adapter checkpoints

#### Scenario: Unsafe final-test permission hard fails
- **WHEN** a pilot config sets `allow_final_test=true`
- **THEN** validation fails before training, optional imports, dev evaluation,
  or report claims are produced

#### Scenario: Tiny budget limits are enforced
- **WHEN** a pilot config sets `max_steps > 20` or `sample_limit > 8`
- **THEN** validation rejects the config before training or optional ML imports

### Requirement: Import-safe backend wiring
The Phase 5D backend module SHALL NOT import torch, transformers, peft,
colpali_engine, or any selected visual backend dependency at module import
time; optional imports SHALL occur only inside the guarded real-training
function after non-import gates have passed.

#### Scenario: Module import is dependency-light
- **WHEN** `visdoc_retrieve.train_lora_pilot` and the Phase 5D backend module
  are imported in a default local environment
- **THEN** the imports succeed without importing or requiring torch,
  transformers, peft, colpali_engine, CUDA, network access, or model weights

#### Scenario: Missing optional dependency blocks clearly
- **WHEN** all non-import gates pass but one or more optional real-training
  dependencies are missing
- **THEN** the launcher records `optional_training_dependency_missing` or an
  equivalent explicit blocked reason and does not execute training

### Requirement: Local-only model loading
The real backend SHALL accept only an existing local model path and SHALL NOT
download models, resolve remote model identifiers, or use network access for
model loading.

#### Scenario: Missing local model path blocks clearly
- **WHEN** real training is requested but `local_model_path` does not exist
- **THEN** the launcher blocks before optional ML imports and records a
  `missing_local_model_path` reason

#### Scenario: Backend uses local files only
- **WHEN** the backend reaches model-loading code
- **THEN** it uses the configured local path with local-files-only behavior and
  does not use the public model name as a network download source

### Requirement: Train-only tiny sample construction
The real backend SHALL build the tiny pilot sample from train split hard
negatives only, cap the effective sample count at `sample_limit <= 8`, and
shall not read final-test files.

#### Scenario: Sample limit constrains train triples
- **WHEN** the train hard-negative file contains more records than the
  configured sample limit
- **THEN** the backend uses no more than the configured sample count and
  records the effective training sample count in evidence

#### Scenario: Final test files are not read
- **WHEN** the pilot backend prepares training and dev sanity evidence
- **THEN** it reads train hard negatives for training samples, may reference dev
  inputs only for dev-only schema/sanity metadata, and does not open final-test
  files

### Requirement: Phase 5D evidence
The system SHALL write Phase 5D environment, safety, run-card, sanitized
adapter-manifest, dev-eval, progress-ledger, and Chinese human-brief evidence
for the actual outcome, whether blocked or pilot-run.

#### Scenario: Blocked evidence is public-safe
- **WHEN** any required gate is unmet
- **THEN** committed Phase 5D evidence records the blocked reason, command,
  GPU/CUDA summary when available, redacted local model path summary, max
  steps, sample limit, final-test exclusion, no adapter/weight/cache commits,
  and no benchmark-improvement claim

#### Scenario: Pilot evidence remains dev-only
- **WHEN** a tiny pilot actually runs
- **THEN** committed evidence records that the run was pilot/dev-only/not final
  benchmark, final test was unused, adapter outputs are under an ignored local
  artifact path, and no pilot loss or dev-only sanity value is claimed as
  retrieval improvement

### Requirement: Existing phase behavior is preserved
The Phase 5D change SHALL preserve existing MVP, hard-negative mining, Phase
5A dry-run, Phase 5B launch-gate, and Phase 5C blocked evidence behavior.

#### Scenario: Existing validation commands still run
- **WHEN** the Phase 5D branch is validated locally
- **THEN** the MVP command, hard-negative mining command, Phase 5A dry-run
  command, Phase 5B/5C pilot-gate blocked command, py_compile, pyproject parse,
  pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check`
  complete or report a truthful blocking reason

#### Scenario: Prior claims remain unchanged
- **WHEN** Phase 5D files are reviewed
- **THEN** existing MVP, hard-negative, Phase 5A, Phase 5B, and Phase 5C reports
  are not rewritten into benchmark, final-test, adapter-improvement, or
  successful-training claims
