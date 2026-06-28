## Context

The user explicitly tried to activate `$opsx-auto`, but the runtime failed
closed because this new repository has no initialized opsx-auto store, no
`.opsx-auto-config/`, no real commit, and no dedicated linked worktree.
`unattended-local-core` also requires config files to be preapproved and
immutable at store initialization time, and it rejects arbitrary validation
commands unless they are bound to a repo-contained script and interpreter hash.

This change prepares the repo-local prerequisites only. It does not initialize
`.opsx-auto/`, does not run the autonomous loop, and does not replace the
current OpenSpec apply flow for active feature work.

## Goals / Non-Goals

**Goals:**

- Add `.opsx-auto-config/unattended-local.json`,
  `.opsx-auto-config/contract.json`, and
  `.opsx-auto-config/validation-policy.json` in a reviewable form.
- Add a repo-contained validation script with a strict shebang and no dynamic
  install, shell pipe, network, model-download, GPU, Git integration, or store
  mutation behavior.
- Bind the validation policy to the exact validation script SHA-256 and the
  exact shebang interpreter path, realpath, and SHA-256 expected by runtime
  validation.
- Bind the contract to a canonical `contract_sha256` and stable goal/evidence
  IDs that a later phase manifest can reference.
- Add documentation that explains how to use the prepared files after an
  initial commit and dedicated linked worktree exist.

**Non-Goals:**

- No `.opsx-auto/` store initialization.
- No runtime `resolve`, `recover`, `finalize-tail-anchor`, phase execution, or
  autonomous local editing.
- No branch creation, worktree creation, staging, commit, merge, push, PR,
  archive, deployment, or external review automation.
- No Phase 2 text retrieval implementation.
- No weakening of the existing project boundaries around final test results,
  visual inference, model downloads, hard-negative mining, or training.

## Decisions

1. Commit concrete config files instead of only prose templates.

   `init-store` requires the three config files to exist under
   `.opsx-auto-config/` and records their hashes. Concrete files make later
   initialization auditable. The alternative, leaving placeholder snippets in
   documentation only, would not unblock runtime initialization.

2. Keep the global allowed paths bounded and project-specific.

   The unattended config will preapprove only paths needed for the next local
   OpenSpec implementation loop: source modules, tests, configs, reports,
   human briefs, docs, relevant OpenSpec change files, and the validation
   script. It must not use `**` as a global catch-all and must not include
   `.git/`, `.opsx-auto/`, or `.opsx-auto-config/` as editable runtime paths.

3. Use a repo validation wrapper as the only validation policy entry point.

   Runtime validation requires `argv[0]` to be a repo-contained script and
   rejects shell-form command strings. A wrapper such as
   `scripts/validate-local-core.sh` can run the existing local baseline in a
   fixed order while keeping the runtime policy simple and hash-bound. The
   alternative, listing `pytest`, `ruff`, `mypy`, and `openspec` directly in
   JSON, would be rejected by the runtime validator.

4. Scope the contract to the next autonomous implementation loop.

   The contract should contain stable core goal and mandatory evidence IDs for
   implementing `add-text-retrieval-baselines` under the established project
   boundaries. Phase manifests can then narrow scope and bind evidence to these
   IDs. The alternative, a vague contract for "all future project work", would
   be too broad for unattended operation.

5. Make remaining bootstrap steps explicit documentation, not automated tasks.

   The repo still needs a real commit and a dedicated linked worktree before
   `init-store` can succeed. This change may document those commands, but it
   must not run them automatically or treat them as completed evidence.

## Risks / Trade-offs

- Hash-bound config is machine-sensitive -> Generate hashes during apply from
  the live repo script and interpreter, then validate them with runtime tools.
- Contract could over-authorize future work -> Keep goals tied to the existing
  Phase 2 proposal and existing project non-goals.
- Config files may be edited after initialization -> Document that changes
  after `init-store` invalidate resume and require a fresh controlled setup.
- Validation wrapper can hide complexity -> Keep it small and limited to the
  existing local validation baseline.
- Current repository cannot complete store init yet -> Treat successful
  config preparation as this change's done state, and leave store init for the
  post-commit dedicated-worktree step.
