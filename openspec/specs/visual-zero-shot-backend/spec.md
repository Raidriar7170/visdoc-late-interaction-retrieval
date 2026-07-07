# visual-zero-shot-backend Specification

## Purpose
TBD - created by archiving change add-visual-zero-shot-backend. Update Purpose after archive.
## Requirements
### Requirement: Explicit visual zero-shot backend config
The system SHALL provide a local visual zero-shot config that explicitly names
the backend, model path or model ID, device, batch size, cache path, corpus
path, query path, and qrels path.

#### Scenario: Example config is local-only and opt-in
- **WHEN** the example visual zero-shot config is inspected
- **THEN** it declares an optional real backend, local model fields, local-only
  execution, cache path, corpus/query/qrels paths, and is not required by CI

#### Scenario: Default MVP config remains mock-only
- **WHEN** the default MVP config is loaded
- **THEN** it still enables deterministic `mock_visual` and does not enable a
  real visual model backend

### Requirement: Import-safe local visual model adapter
The system SHALL expose a local visual-model backend adapter that can be
imported without importing optional model runtimes, downloading weights,
opening network connections, or requiring GPU hardware.

#### Scenario: Adapter import has no heavyweight side effects
- **WHEN** default tests import the real backend adapter module
- **THEN** no model weights are downloaded, no network access is required, and
  no GPU runtime is required

#### Scenario: Runtime dependencies are loaded only for real execution
- **WHEN** a user runs `--check-config` or `--dry-run`
- **THEN** the command validates config and corpus paths without importing
  optional ColPali / ColQwen runtime libraries

### Requirement: Missing local model path fails clearly
The system SHALL fail clearly when a configured real backend references a local
model path that does not exist.

#### Scenario: Missing model path is not reported as success
- **WHEN** a real visual zero-shot config points to a missing local model path
- **THEN** config checking reports a clear missing-path error and does not
  fall back to `mock_visual`

### Requirement: Optional visual zero-shot CLI
The system SHALL provide an optional CLI for visual zero-shot smoke that can
check config, dry-run preflight, or attempt a local real backend run only when
explicitly invoked.

#### Scenario: Check-config validates without execution
- **WHEN** `PYTHONPATH=src python -m visdoc_retrieve.run_visual_zero_shot --config configs/visual_zero_shot.local.example.json --check-config` is run
- **THEN** the command validates the config shape and local path policy without
  running model inference or writing benchmark claims

#### Scenario: Real execution cannot be faked
- **WHEN** the optional CLI is invoked for a real run and the local runtime or
  model path is unavailable
- **THEN** the command exits with a clear error instead of writing a successful
  real visual retrieval result

### Requirement: Real visual embedding cache schema
The system SHALL define a token-embedding cache schema that can store real
visual backend query/page token embeddings with backend provenance and shape
metadata compatible with MaxSim scoring.

#### Scenario: Real cache round-trips token embeddings
- **WHEN** a real visual token embedding cache is written and loaded
- **THEN** the loaded cache preserves backend name, model reference, embedding
  dimensions, query/page IDs, token counts, and embedding values

#### Scenario: Cache shape validation rejects invalid embeddings
- **WHEN** a real visual cache contains mismatched token embedding dimensions
- **THEN** loading the cache fails instead of passing invalid data to MaxSim

### Requirement: Visual zero-shot checkpoint boundaries
The system SHALL document that this checkpoint is optional local smoke only
and SHALL NOT claim training, hard-negative mining, final-test evaluation, or
benchmark improvement.

#### Scenario: Human brief and ledger record boundaries
- **WHEN** the visual zero-shot backend checkpoint docs are inspected
- **THEN** they state that the real backend is optional/local only, the default
  mock is not real ColPali / ColQwen, no training occurred, no hard-negative
  mining occurred, no final-test evaluation occurred, and no benchmark
  improvement is claimed
