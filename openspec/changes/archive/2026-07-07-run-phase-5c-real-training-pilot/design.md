## Context

Phase 5C starts after the Phase 5B launch gate is merged to `main`. The
existing launcher already validates final-test exclusion, tiny budget,
hard-negative inputs, ignored adapter output, environment permission, local
model path presence, and CUDA availability before it can enter the guarded
real-training path. The user has authorized an A100/local-model pilot attempt,
but the true remote repository path and true local model path are private
inputs that must not be committed.

The Phase 5B code also intentionally treats the real backend as a guarded
scaffold. If the current environment cannot satisfy the exact private path
preconditions, or if the launcher reports the backend is not wired for real
adapter creation, Phase 5C must record a blocked checkpoint rather than
turning the dry-run or scaffold into a training claim.

## Goals / Non-Goals

**Goals:**

- Start from clean `origin/main` in a dedicated branch/worktree.
- Prepare a local-only pilot config with `allow_real_training=true`,
  `allow_final_test=false`, `VISDOC_ENABLE_REAL_TRAINING=1`, `max_steps <= 20`,
  a sample limit no larger than 8 triples when supported by the current
  launcher, and an ignored adapter output directory.
- Attempt the existing pilot launcher only when path and device prerequisites
  can be truthfully checked.
- Commit only sanitized Phase 5C metadata/report evidence, including whether
  the pilot ran or blocked, redacted local-model-path status, GPU/CUDA summary,
  max steps, final-test exclusion, and no-claim/no-artifact boundaries.
- Preserve existing Phase 5A/5B claims and deterministic validation behavior.

**Non-Goals:**

- Implement a full production training backend, broaden the project into a RAG
  chatbot, deploy, merge, or archive this OpenSpec change.
- Download or resolve model weights over the network.
- Commit adapter checkpoints, model weights, caches, logs, tensorboard or wandb
  directories, private local config, or private machine paths.
- Run final test data or report benchmark improvement, model superiority, or
  adapter effectiveness.

## Decisions

1. **Use a blocked checkpoint when private inputs are unavailable.**
   The prompt includes placeholders for the remote repository path and local
   model path. If those placeholders cannot be resolved to existing paths inside
   the A100 environment, the correct Phase 5C outcome is blocked evidence.
   Alternative: infer a model path from unrelated local model directories.
   Rejected because guessing would violate the local-model-path gate and could
   create misleading model identity evidence.

2. **Keep private config local and commit sanitized reports only.**
   The real or attempted pilot config lives under ignored local artifacts, while
   committed Phase 5C reports replace the private model path with a redacted
   placeholder and record only high-level device/config status. Alternative:
   commit the exact pilot config. Rejected because the model path is private and
   may identify machine-local storage.

3. **Do not convert Phase 5B scaffold behavior into a success.**
   If all gates pass but the launcher returns a scaffold-only blocked result,
   Phase 5C records that blocked code and does not create an adapter manifest
   that claims a checkpoint exists. Alternative: fabricate an adapter manifest
   to satisfy downstream reports. Rejected because no model artifact may be
   invented or committed.

4. **Separate dev-only schema from benchmark metrics.**
   Phase 5C may emit a dev-eval schema or explicit dev-eval record, but metrics
   remain null/not-run unless a real adapter exists and a scoped dev sanity
   evaluation is implemented. Final test remains unused in every outcome.

## Risks / Trade-offs

- **Risk: Blocked evidence looks like failure rather than progress.** →
  Mitigation: run-card and human brief state that blocked is the truthful
  outcome when a private path, CUDA gate, or scaffold gate cannot be satisfied.
- **Risk: A private model path leaks through generated JSON.** → Mitigation:
  scan committed files for placeholder/private path patterns and commit only
  redacted summaries.
- **Risk: Adapter outputs are accidentally staged.** → Mitigation: keep
  adapter output under ignored local artifacts and run explicit forbidden-file
  scans before commit.
- **Risk: Remote GPU evidence is overclaimed.** → Mitigation: record only the
  observed GPU/CUDA availability summary and whether training actually started;
  do not report pilot loss as model improvement.
