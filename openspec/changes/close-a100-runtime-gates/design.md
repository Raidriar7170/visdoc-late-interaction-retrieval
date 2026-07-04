## Context

Phase 5F converted the A100 runtime readiness problem into structured gates:
allowed-root placement, dependency importability, CUDA/GPU visibility, and exact
A100-readable model-path readiness. A fresh read-only probe found the remote
checkout under `/mnt/data/minghongsun/visdoc-late-interaction-retrieval`, CUDA
with eight A100 GPUs, and idle candidates, but also found that
`colpali_engine` is not importable in the checked Python runtime and
`/mnt/data/minghongsun/models/vidore-colqwen2-v1.0-hf` is absent.

This phase is a closure attempt for runtime gates, not a real-training pilot.
It may prepare an allowed-root runtime environment and record the result, but
it must not download model weights, launch training, create adapters, or turn
missing prerequisites into success language.

## Goals / Non-Goals

**Goals:**

- Create or reuse an isolated Python runtime and cache/temp roots under
  `/mnt/data/minghongsun`.
- Attempt to close the `colpali_engine` importability gate without writing
  package artifacts under `/root`, `/tmp`, or another user's directory.
- Re-check the exact model path
  `/mnt/data/minghongsun/models/vidore-colqwen2-v1.0-hf` and record redacted
  readiness or a precise blocker.
- Generate Phase 5G closure evidence, progress-ledger status, and a concise
  Chinese Human Brief that state whether the runtime is `runtime_ready`,
  `blocked`, or `needs_user_input`.

**Non-Goals:**

- Do not run `train_lora_pilot` or any training workload.
- Do not download, resolve, or synthesize model weights.
- Do not create adapters, checkpoints, training caches, final-test metrics, or
  benchmark tables.
- Do not write project files, logs, caches, or temporary files outside
  `/mnt/data/minghongsun`.
- Do not infer model readiness from unrelated model directories.

## Decisions

1. **Make closure evidence a new phase on the existing preflight helper.**
   The existing `a100_preflight` helper already redacts paths and separates
   runtime readiness from training success. Extending it with Phase 5G evidence
   keeps the truth surface focused and avoids a second remote-runner abstraction.

2. **Treat dependency setup as an allowed-root, best-effort closure attempt.**
   The phase may create an allowed-root venv or userbase and run dependency
   installation with cache and temp paths under `/mnt/data/minghongsun`. If the
   install attempts to pull incompatible heavy dependencies, fails, or cannot
   leave `colpali_engine` importable, the committed evidence records the
   blocker instead of retrying broadly.

3. **Treat model path closure as verification only.** The exact expected path is
   checked on the A100 host, and shape markers are recorded in redacted form.
   If the directory remains absent, the phase records `missing_local_model_path`
   or `needs_user_model_path`; it does not download from HuggingFace or scan
   unrelated private model directories to claim readiness.

4. **Ready means gates only.** Even if all runtime gates close, Phase 5G reports
   `training_launched=false`, no model download, no adapter checkpoint, no
   final-test use, and no benchmark-improvement claim.

## Risks / Trade-offs

- **Dependency install may be blocked by package resolution or large wheels** ->
  use an allowed-root isolated runtime and record the precise dependency blocker
  if importability cannot be closed.
- **Model path may remain absent** -> preserve a truthful blocked outcome and
  make the next required user action explicit instead of widening this phase
  into model download or transfer.
- **GPU availability can change between preflight and pilot** -> record only a
  fresh observation and safe idle candidates; do not reserve or launch jobs.
- **Closure wording can overstate success** -> keep run-card, safety JSON, and
  Human Brief language explicit that this is runtime-gate evidence only.
