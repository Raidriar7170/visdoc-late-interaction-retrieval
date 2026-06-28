## 1. Validation Wrapper

- [x] 1.1 Add a repo-contained validation script, such as `scripts/validate-local-core.sh`, with a strict absolute shebang.
- [x] 1.2 Keep the validation script limited to local baseline checks and exclude package installs, shell pipes, network access, model downloads, GPU/A100 requirements, `.opsx-auto/` mutation, staging, commit, merge, push, archive, or deployment.
- [x] 1.3 Run the validation script directly and confirm it passes or document any existing baseline failure without weakening the script.
- [x] 1.4 Compute the validation script SHA-256 and the live shebang interpreter path, realpath, and SHA-256 needed by `validation-policy.json`.

## 2. Preapproved Config Files

- [x] 2.1 Add `.opsx-auto-config/unattended-local.json` with mode `unattended-local-core`, bounded `allowed_paths`, `.opsx-auto-inbox/*.json` phase discovery, watchdog limits, and local validation profile names.
- [x] 2.2 Add `.opsx-auto-config/contract.json` with stable goal IDs, mandatory evidence requirement IDs, project boundary statements, and a self-consistent canonical `contract_sha256`.
- [x] 2.3 Add `.opsx-auto-config/validation-policy.json` with the hash-bound validation profile referencing the repo-contained validation script.
- [x] 2.4 Add focused tests or a small verification helper that parses all three config files as strict JSON and checks required fields, bounded path rules, mandatory evidence requirements, and hash consistency.

## 3. Documentation And Boundaries

- [x] 3.1 Document the remaining manual bootstrap sequence: initial commit, dedicated linked worktree, `init-store`, and bounded phase manifest creation.
- [x] 3.2 Document that this change prepares config only and does not activate `$opsx-auto`, run `resolve`, initialize `.opsx-auto/`, create a worktree, stage, commit, merge, push, or archive.
- [x] 3.3 Update `reports/progress-ledger.yaml` or a focused opsx-auto readiness note to record that auto prerequisites are prepared but the runtime store is not initialized.
- [x] 3.4 Generate a concise Chinese Human Brief for this prerequisite phase under `docs/human-briefs/`.

## 4. Runtime-Oriented Verification

- [x] 4.1 Run `python /Users/raidriar/.codex/skills/opsx-auto/scripts/opsx-auto-runtime.py inspect --repo-root . --mode unattended-local-core` and confirm `.opsx-auto-config` is no longer reported missing.
- [x] 4.2 Run a targeted contract-hash validation check using the opsx-auto runtime library or a repo helper.
- [x] 4.3 Confirm `.opsx-auto/loop-state.json`, `.opsx-auto/genesis-state.json`, and event ledger files were not created.
- [x] 4.4 Confirm `init-store` is not treated as completed in this phase unless the repo is already in a clean dedicated linked worktree with a real HEAD commit.

## 5. Standard Validation And Scope Review

- [x] 5.1 Run `pytest -q` and confirm all tests pass.
- [x] 5.2 Run `ruff check .` and confirm linting passes.
- [x] 5.3 Run `mypy src` and confirm typing passes.
- [x] 5.4 Run `openspec validate --all --strict` and confirm OpenSpec validation passes.
- [x] 5.5 Run `git diff --check` and confirm no whitespace errors.
- [x] 5.6 Review the final diff to confirm it contains only opsx-auto prerequisite config, validation wrapper, documentation, and focused verification; no Phase 2 retrieval implementation, visual inference, training, final test evaluation, or benchmark claims.
