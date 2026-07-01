## Context

Phase 5B begins after the Phase 5A training-readiness dry run has frozen hard
negative inputs and safety evidence. The next step is not a benchmark or
performance claim; it is a launch gate that can either run a tiny real pilot
only under explicit local conditions or produce blocked evidence that explains
why training did not run. Default validation must remain local-only, CPU-safe,
and free of torch, transformers, peft, ColPali/ColQwen, CUDA, model downloads,
network access, model weights, adapter checkpoints, and final-test data.

## Goals / Non-Goals

**Goals:**

- Parse and validate a Phase 5B local pilot config with explicit training,
  final-test, local-model, adapter-output, budget, and report fields.
- Add an environment gate that blocks unless all real-training preconditions
  are satisfied: config permission, final-test disabled, environment variable
  enabled, local model path present, CUDA available, tiny budget, ignored
  adapter output directory, and pilot/dev-only run-card wording.
- Generate blocked evidence by default: `environment-check.json`,
  `blocked-run-card.md`, `safety-check.json`, `dev-eval-schema.json`, and
  `adapter-manifest.example.json`.
- Keep optional ML imports inside the guarded real pilot path so module import,
  default CLI checks, and default tests require no optional training
  dependencies.
- Provide a dev-only evaluation hook that can record `status=not_run` and null
  metrics without pretending that a real adapter exists or improved retrieval.
- Record a concise Chinese human brief and progress-ledger Phase 5B entry that
  preserve no-final-test, no-benchmark-claim, no-adapter-commit boundaries.

**Non-Goals:**

- Downloading model weights, using network access, or resolving remote model
  identifiers.
- Running final test evaluation or writing final-test metrics.
- Claiming benchmark improvement, model superiority, or adapter effectiveness.
- Committing model weights, adapter checkpoints, training caches, tensorboard
  logs, wandb runs, or checkpoint directories.
- Broadening the project into a chatbot, production RAG system, QA generator,
  or generic agent workflow.

## Decisions

1. **Make the blocked path the default CLI behavior.**
   The example config sets `allow_real_training=false`, and the CLI returns a
   clear blocked status with exit code `2` rather than crashing. Alternative:
   make the default command a no-op with exit code `0`. Rejected because the
   validation command should prove the launch gate is active and explain why
   real training did not run.

2. **Represent gates as structured evidence before any real-training import.**
   The CLI writes `environment-check.json` and run-card evidence from
   standard-library checks first. Optional imports happen only in the guarded
   launcher function after all non-import gates pass. Alternative: import torch
   at module load and then decide. Rejected because default tests must not
   require optional ML dependencies.

3. **Require local paths and fail closed on final-test permission.**
   `allow_final_test=true` is a hard configuration error. Missing
   `local_model_path`, missing CUDA, absent `VISDOC_ENABLE_REAL_TRAINING=1`,
   over-budget `max_steps`, and non-ignored adapter output all block before
   training. Alternative: auto-disable final test or silently fall back to
   dry-run behavior. Rejected because that would blur blocked evidence with
   successful launch evidence.

4. **Keep dev evaluation schema separate from performance claims.**
   The dev hook emits `status=not_run` with null metrics when no real adapter
   exists. It validates only dev-scoped input paths and records that final test
   was not used. Alternative: copy mock visual/MVP metrics into the pilot
   report. Rejected because mock or dry-run metrics must not be presented as
   adapter results.

5. **Use ignored artifact paths for real outputs and committed examples for
   review evidence.**
   The committed `reports/training-pilot/` files are small deterministic
   evidence artifacts from the blocked/default path. Real adapter outputs,
   model weights, caches, checkpoints, wandb, and tensorboard paths are ignored.
   Alternative: write pilot outputs under committed report paths. Rejected
   because real artifacts must not be accidentally committed.

## Risks / Trade-offs

- **Risk: Users confuse blocked evidence with a failed implementation.** →
  Mitigation: run-cards and the human brief state that default blocked status
  is expected unless every real-training gate is explicitly satisfied.
- **Risk: Optional dependency checks become environment-specific.** →
  Mitigation: default tests assert import guarding and blocked evidence without
  requiring torch/CUDA; CUDA checks are injectable for tests.
- **Risk: Ignore checks miss a future adapter path.** → Mitigation: tests
  exercise the configured adapter output path with `git check-ignore`.
- **Risk: A future real pilot is overclaimed.** → Mitigation: pilot run-card,
  dev-eval schema, safety check, and ledger all keep `pilot`, `dev-only`, and
  `not final benchmark` language explicit.
