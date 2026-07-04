## Context

Phase 5E added `visdoc_retrieve.a100_preflight`, which accepts structured A100
observations and emits sanitized readiness, safety, and run-card evidence. The
current Phase 5E evidence is still blocked: `colpali_engine` is missing and no
exact A100-readable ColPali / ColQwen `local_model_path` has been provided.

Phase 5F should narrow the next step to runtime-gate materialization. It should
make the two remaining gates explicit and repeatable, while preserving the
public truth surface that no real training, model download, adapter checkpoint,
final-test evaluation, or benchmark claim has happened.

## Goals / Non-Goals

**Goals:**

- Add Phase 5F evidence semantics for optional dependency importability,
  allowed-root runtime/cache placement, exact local model-path readiness, and
  safe idle-GPU observation.
- Reuse the existing structured-observation pattern so committed evidence is
  deterministic and redacted rather than raw SSH logs.
- Record a truthful status: `runtime_ready`, `blocked`, or
  `needs_user_input`.
- Generate repo-local Phase 5F reports, progress-ledger entry, and a concise
  Chinese Human Brief.

**Non-Goals:**

- Do not run `train_lora_pilot` in real-training mode.
- Do not download model weights, resolve remote model IDs, or install system
  packages.
- Do not write project files, logs, caches, checkpoints, or temp outputs under
  `/root`, `/tmp`, or another user's directory.
- Do not create adapters/checkpoints, read final test data, or claim retrieval
  improvement.
- Do not silently infer a model path from broad private directory scans.

## Decisions

1. **Use a Phase 5F schema on the existing preflight helper.** The runtime gate
   is a continuation of `a100-real-training-preflight`, so extending
   `a100_preflight.py` keeps evidence generation in one focused module instead
   of introducing a parallel remote-runner abstraction.

2. **Treat dependency installation as observed state, not an imperative action.**
   Phase 5F evidence may report that an isolated environment exists and that
   `colpali_engine` is importable or missing, but the local helper does not run
   package installation. This keeps the committed code deterministic and avoids
   hidden network/system writes.

3. **Model path readiness requires an exact provided path.** The evidence can
   verify shape signals such as existence and expected model-file markers from
   a structured observation, but it must not commit the exact private path or
   guess from unrelated directories.

4. **Ready means gates only, not training success.** If dependency, model path,
   CUDA, and idle-GPU gates are all clear, Phase 5F may report
   `runtime_ready`; it still must report `training_launched=false` and no
   benchmark or checkpoint side effects.

## Risks / Trade-offs

- **A package import can be absent for environment-specific reasons** ->
  record `optional_dependency_missing` with the checked environment summary
  instead of forcing setup in committed code.
- **A provided model path may be private or stale** -> commit only redacted
  existence and coarse file-shape status; keep `needs_user_input` or
  `missing_local_model_path` explicit when necessary.
- **GPU availability can change after preflight** -> treat idle-GPU candidates
  as observation evidence for a later pilot proposal, not a reservation or job
  launch.
- **Runtime-ready wording could be mistaken for training success** -> keep
  safety flags and Human Brief language explicit: no training, no downloads, no
  final test, no checkpoint, no benchmark claim.
