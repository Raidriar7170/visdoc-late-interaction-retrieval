## ADDED Requirements

### Requirement: Pilot config validation
The system SHALL provide a local-only Phase 5B pilot config that declares
model identity, local model path, adapter output directory, hard-negative
inputs, corpus/query/qrels inputs, candidate-universe identity, loss type,
LoRA/QLoRA hyperparameters, batch parameters, tiny budget, seed, device,
training permission, final-test permission, adapter-save behavior, and report
paths.

#### Scenario: Example pilot config parses without optional ML dependencies
- **WHEN** `configs/train_lora_pilot.local.example.json` is loaded
- **THEN** it records the configured fields without requiring torch,
  transformers, peft, ColPali/ColQwen, CUDA, network access, model downloads,
  or local model weights

#### Scenario: Final test permission hard fails
- **WHEN** the pilot config sets `allow_final_test` to true
- **THEN** validation fails before environment checks, training, dev
  evaluation, or report claims are produced

#### Scenario: Over-budget pilot hard fails
- **WHEN** the pilot config sets a real-training budget greater than the
  allowed tiny pilot budget
- **THEN** validation rejects the config before training or optional ML imports

### Requirement: Real-training launch gate
The system SHALL expose
`PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot --config configs/train_lora_pilot.local.example.json`
as a local-only launch gate that executes real pilot training only when every
configured and environmental precondition is satisfied.

#### Scenario: Default config blocks clearly
- **WHEN** the pilot CLI is run with the committed example config
- **THEN** it does not execute training, exits with a clear blocked status, and
  writes `reports/training-pilot/environment-check.json` plus
  `reports/training-pilot/blocked-run-card.md`

#### Scenario: Missing local model path blocks clearly
- **WHEN** real training is otherwise requested but `local_model_path` does not
  exist
- **THEN** the CLI blocks before optional ML imports and records
  `missing_local_model_path` or an equivalent explicit blocked reason

#### Scenario: CUDA unavailable blocks clearly
- **WHEN** real training is otherwise requested but CUDA is unavailable
- **THEN** the CLI blocks before training and records `cuda_unavailable` or an
  equivalent explicit blocked reason

#### Scenario: All gates are required before real pilot
- **WHEN** config allows real training, final test remains false,
  `VISDOC_ENABLE_REAL_TRAINING=1` is set, the local model path exists, CUDA is
  available, `max_steps <= 20`, the adapter output path is ignored, and the
  run-card is marked pilot/dev-only/not-final-benchmark
- **THEN** the CLI may enter the guarded real pilot launcher; otherwise it
  SHALL block without executing training

### Requirement: Guarded optional imports
The pilot launcher SHALL keep optional torch, transformers, peft, and
ColPali/ColQwen imports inside the guarded real pilot function so importing the
module and running default validation do not require those packages.

#### Scenario: Module import is dependency-light
- **WHEN** `visdoc_retrieve.train_lora_pilot` is imported in a default local
  environment
- **THEN** the import succeeds without importing or requiring torch,
  transformers, peft, or colpali_engine

#### Scenario: Blocked path does not import optional training libraries
- **WHEN** the CLI blocks because a non-import gate is unmet
- **THEN** no torch, transformers, peft, or colpali_engine import is required
  to generate blocked evidence

### Requirement: Dev-only evaluation schema
The system SHALL generate a dev-only evaluation schema for Phase 5B that reads
only dev-scoped inputs, records final-test exclusion, and does not fabricate
adapter metrics or improvement claims when no real adapter exists.

#### Scenario: No adapter records not-run null metrics
- **WHEN** no real adapter was produced by a gated pilot
- **THEN** `reports/training-pilot/dev-eval-schema.json` records
  `status=not_run`, null metrics, dev-only scope, and `final_test_used=false`

#### Scenario: Final test paths are rejected
- **WHEN** a dev evaluation hook is configured with a final-test input path or
  `allow_final_test=true`
- **THEN** validation fails before evaluation output is treated as pilot
  evidence

### Requirement: Adapter manifest schema
The system SHALL generate an adapter manifest example for Phase 5B review that
records adapter output directory, base model identity, model revision,
hard-negative artifact hash, training config hash, git commit, max steps, seed,
device, `final_test_used=false`, created timestamp, and pilot status.

#### Scenario: Blocked run writes manifest example without adapter claim
- **WHEN** the default pilot CLI blocks before training
- **THEN** `reports/training-pilot/adapter-manifest.example.json` exists with
  `pilot_status` indicating blocked or not run and without claiming that an
  adapter checkpoint was created

### Requirement: Safety evidence and artifact boundaries
The Phase 5B pilot gate SHALL record safety evidence and repository boundaries
showing that default validation did not run training, download models, use
network access, use final test data, commit weights/adapters, or claim
benchmark improvement.

#### Scenario: Safety check records no-training boundaries
- **WHEN** the default blocked pilot command completes
- **THEN** `reports/training-pilot/safety-check.json` records no training
  executed, no model download, no network use, no final test, no adapter or
  model weights committed, no benchmark claim, and no mock visual result
  presented as a real visual result

#### Scenario: Real artifact paths are ignored
- **WHEN** the configured adapter output path, model-weight paths, training
  caches, checkpoints, tensorboard logs, or wandb directories are checked
- **THEN** they are ignored by git and not included as committed artifacts

### Requirement: Project evidence and prior behavior preservation
The Phase 5B change SHALL add reviewer-readable evidence while preserving the
existing deterministic MVP command, hard-negative mining command, and Phase 5A
dry-run command.

#### Scenario: Existing CLIs remain valid
- **WHEN** the MVP command, hard-negative mining command, and Phase 5A dry-run
  command are run after Phase 5B support is added
- **THEN** they still succeed with deterministic local behavior and do not
  require GPU hardware, model downloads, optional training dependencies,
  final-test evaluation, or real training

#### Scenario: Human brief and ledger describe Phase 5B
- **WHEN** Phase 5B artifacts are inspected
- **THEN** a concise Chinese human brief under `docs/human-briefs/` and a
  `reports/progress-ledger.yaml` Phase 5B entry explain what changed, the
  training gates, why default validation blocks, how to run a future A100/local
  model pilot, dev-only selection, final-test exclusion, no benchmark claim,
  no committed adapters or weights, and the recommended next step
