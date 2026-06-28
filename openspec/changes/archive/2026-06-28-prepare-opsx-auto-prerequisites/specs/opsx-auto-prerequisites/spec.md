## ADDED Requirements

### Requirement: Preapproved opsx-auto config files
The repository SHALL provide `.opsx-auto-config/unattended-local.json`,
`.opsx-auto-config/contract.json`, and
`.opsx-auto-config/validation-policy.json` as strict JSON inputs for a later
`unattended-local-core` store initialization.

#### Scenario: Required config files exist
- **WHEN** the prerequisite preparation change is applied
- **THEN** all three required `.opsx-auto-config/` JSON files exist in the repository root and contain valid JSON objects

#### Scenario: Config preparation does not initialize store
- **WHEN** the prerequisite preparation change is applied
- **THEN** it does not create `.opsx-auto/loop-state.json`, `.opsx-auto/genesis-state.json`, or any runtime event ledger

### Requirement: Bounded unattended edit scope
The unattended-local config SHALL preapprove only bounded repo-relative edit
paths needed for the next local OpenSpec implementation loop and SHALL NOT
preapprove `.git/`, `.opsx-auto/`, `.opsx-auto-config/`, absolute paths, parent
directory traversal, or global catch-all scopes.

#### Scenario: Allowed paths are bounded
- **WHEN** `.opsx-auto-config/unattended-local.json` is inspected
- **THEN** `allowed_paths` is a non-empty array of bounded repo-relative patterns with literal first path segments and without a global `**` catch-all

#### Scenario: Runtime metadata paths are not editable
- **WHEN** `.opsx-auto-config/unattended-local.json` is inspected
- **THEN** `.git/`, `.opsx-auto/`, and `.opsx-auto-config/` are not included in `allowed_paths`

### Requirement: Hash-bound validation policy
The validation policy SHALL reference a repo-contained validation script and
bind that script plus its shebang interpreter with SHA-256 hashes required by
the opsx-auto runtime validator.

#### Scenario: Validation profile binds script and interpreter
- **WHEN** `.opsx-auto-config/validation-policy.json` is inspected
- **THEN** the completion validation profile includes `argv`, `repo_script_sha256`, `shebang_interpreter_path`, `shebang_interpreter_realpath`, `shebang_interpreter_sha256`, and `timeout_seconds`

#### Scenario: Validation wrapper remains local-only
- **WHEN** the repo-contained validation script is inspected
- **THEN** it runs only local validation commands and does not install packages, use shell pipes, access the network, download models, require GPU/A100 hardware, mutate `.opsx-auto/`, stage files, commit, merge, push, or archive changes

### Requirement: Contract goal and evidence binding
The opsx-auto contract SHALL define stable goal IDs and mandatory evidence
requirement IDs for the next bounded autonomous implementation loop, and SHALL
include a canonical `contract_sha256`.

#### Scenario: Contract contains mandatory evidence
- **WHEN** `.opsx-auto-config/contract.json` is inspected
- **THEN** every core goal has at least one mandatory evidence requirement with stable IDs that a phase manifest can reference

#### Scenario: Contract hash is self-consistent
- **WHEN** the opsx-auto runtime contract hash validator is run against `.opsx-auto-config/contract.json`
- **THEN** the embedded `contract_sha256` matches the canonical immutable contract payload

### Requirement: Bootstrap boundary documentation
The repository SHALL document the remaining human-controlled steps required
after config preparation: initial commit, dedicated linked worktree, runtime
`init-store`, and bounded phase manifest creation.

#### Scenario: Documentation separates preparation from activation
- **WHEN** a reader reviews the opsx-auto prerequisite documentation
- **THEN** it states that this change prepares config only and does not activate `$opsx-auto`, run `resolve`, initialize `.opsx-auto/`, create a worktree, stage, commit, merge, push, or archive

### Requirement: Existing project boundaries remain intact
The opsx-auto prerequisite preparation SHALL NOT implement Phase 2 retrieval
code, visual inference, hard-negative mining, training, final test evaluation,
or benchmark improvement claims.

#### Scenario: Preparation does not expand retrieval scope
- **WHEN** the prerequisite preparation change is reviewed
- **THEN** it is limited to opsx-auto config, validation wrapper, documentation, and focused verification for those surfaces
