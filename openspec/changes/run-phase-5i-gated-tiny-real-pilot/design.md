## Context

Phase 5D added the guarded `train_lora_pilot` launcher and Phase 5H closed the
A100 model-path gate with static marker evidence. The next bounded step is not
another preflight; it is one tiny real-pilot attempt on the A100 runtime with
the exact local model path, explicit training permission, CUDA visibility, and
strictly ignored local outputs.

The current launcher still hard-codes Phase 5D public metadata such as schema
IDs, report titles, run-card names, and the progress-ledger section. That is
good enough for the Phase 5D blocked example, but it cannot truthfully emit
Phase 5I evidence from an untracked local config without either overloading the
5D artifact surface or editing committed evidence by hand after the run.

The repo-local `opsx-auto practical` inputs are also stale: the allowed edit
paths still point at older changes, and the phase-manifest glob does not match
the repository's current YAML manifest convention. If left untouched, the
runtime will fail closed before the new Phase 5I loop can begin.

## Goals / Non-Goals

**Goals:**

- Start Phase 5I from clean `origin/main` in a dedicated local branch/worktree
  and a dedicated remote A100 worktree.
- Keep the actual A100 pilot config untracked under `local/` while committing
  only sanitized Phase 5I evidence.
- Parameterize the public reporting layer so Phase 5I can emit its own phase
  schema/title/ledger identity while Phase 5D default behavior stays intact.
- Attempt one tiny real pilot only when the launcher gates, A100 model path,
  CUDA/GPU, optional dependencies, and ignored adapter output are all ready.
- Preserve truthful blocked evidence when the pilot cannot safely run.

**Non-Goals:**

- Do not change the guarded real-training algorithm, budget caps, metrics, or
  benchmark semantics.
- Do not download model weights or use network model resolution.
- Do not commit adapter checkpoints, model weights, caches, logs, exact private
  model paths, or local private config contents.
- Do not merge, deploy, or archive this OpenSpec change.

## Decisions

1. **Parameterize only the public evidence layer.**
   The training launcher already enforces the important safety gates. Phase 5I
   only needs a small extension so config can override the public phase metadata
   for schemas, titles, and ledger section names. Alternative: clone the
   launcher into a separate Phase 5I module. Rejected because that would
   duplicate gate logic and increase drift risk.

2. **Keep the real pilot config local and ignored.**
   The committed repo will add `local/` to `.gitignore`, and the Phase 5I pilot
   config will live at `local/train_lora_pilot.phase5i.local.json` only in the
   execution worktrees. Alternative: commit a sanitized Phase 5I config.
   Rejected because the exact local model path is private and should not be
   versioned.

3. **Use the existing guarded launcher on the A100 side without widening the
   scope.**
   The actual pilot command stays `PYTHONPATH=src python -m
   visdoc_retrieve.train_lora_pilot --config <local-config>`, with
   `VISDOC_ENABLE_REAL_TRAINING=1`, `allow_real_training=true`,
   `allow_final_test=false`, `max_steps <= 20`, `sample_limit <= 8`, and an
   ignored adapter output dir. Alternative: add a new special-purpose A100
   launcher. Rejected because the existing launcher already owns the safety
   contract.

4. **Refresh only the minimal `opsx-auto practical` inputs needed for Phase 5I.**
   Update the allowed-path and phase-manifest-glob settings, plus the tracked
   goal/manifest inputs, but leave `.opsx-auto/` runtime state untracked and
   runtime-owned. Alternative: ignore the stale `opsx-auto` inputs and work
   entirely outside the loop. Rejected because the user explicitly invoked
   `/opsx auto practical`.

## Risks / Trade-offs

- **Stale runtime config blocks the practical loop** -> Refresh only the
  minimal tracked `opsx-auto` inputs and verify the runtime can inspect/init
  from the dedicated worktree.
- **A100 pilot still blocks despite Phase 5H closure** -> Preserve blocked
  evidence as the truthful outcome and keep the branch PR-ready without
  widening into manual environment surgery.
- **Private path leakage through generated evidence** -> Keep the config local,
  reuse redacted model-path summaries, and scan committed files before commit.
- **Adapter outputs or caches are accidentally staged** -> Keep adapter output
  under ignored local artifacts and run explicit safety/forbidden-artifact
  checks plus `git diff --check`.
