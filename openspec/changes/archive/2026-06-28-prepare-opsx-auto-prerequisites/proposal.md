## Why

`opsx-auto` cannot run in this repository yet because the runtime requires
preapproved config files, a pinned validation script, a real commit, and a
dedicated linked worktree before store initialization. This change prepares the
repo-local configuration and validation surfaces needed for a later supervised
`init-store`, without starting the autonomous loop.

## What Changes

- Add repo-local `.opsx-auto-config/` files for unattended-local-core:
  `unattended-local.json`, `contract.json`, and `validation-policy.json`.
- Add a pinned repo-contained validation script that runs the local validation
  baseline without shell pipes, installs, network access, model downloads, GPU
  requirements, staging, commit, merge, push, or store mutation.
- Bind `validation-policy.json` to the validation script hash and the script
  shebang interpreter hash required by the opsx-auto runtime.
- Bind `contract.json` to a canonical contract hash and explicit mandatory
  evidence requirements for the next autonomous implementation phase.
- Document the remaining human-controlled bootstrap steps: create an initial
  commit, create a dedicated linked worktree, run `init-store`, then provide
  bounded phase manifests.
- Keep `.opsx-auto/` store initialization, phase execution, branch/worktree
  creation, staging, commit, merge, push, external review, and automatic
  archive out of this change.

## Capabilities

### New Capabilities

- `opsx-auto-prerequisites`: Defines repo-local opsx-auto config, pinned
  validation policy, contract binding, and non-autonomous bootstrap boundaries.

### Modified Capabilities

- None.

## Impact

- Affected files: `.opsx-auto-config/`, `scripts/`, focused validation tests or
  checks, and documentation under `docs/` or `reports/`.
- Affected workflow: enables a later human-controlled `opsx-auto-runtime.py
  init-store --mode unattended-local-core` attempt after the repo has a real
  commit and is opened through a dedicated linked worktree.
- No automatic editing, `.opsx-auto/` store write, Git integration, OpenSpec
  archive, release action, model download, GPU/A100 job, or Phase 2 retrieval
  implementation is introduced by this change.
