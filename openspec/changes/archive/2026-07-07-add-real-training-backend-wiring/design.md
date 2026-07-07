## Context

Phase 5B added the launch gate and Phase 5C attempted the pilot checkpoint,
but the real-training path still returns `real_training_backend_scaffold_only`
after all gates pass. Phase 5D must turn that scaffold into a local-only,
optional-dependency guarded backend wiring checkpoint without changing the
default validation contract: no GPU, no torch/transformers/peft/ColPali,
no model downloads, no final-test evaluation, and no committed model artifacts.

The existing `training_pilot.py` already owns config parsing, gate evaluation,
evidence writing, run-card generation, and progress-ledger updates. The safest
shape is to keep those public surfaces stable and isolate backend execution in
a new module that has no top-level ML imports.

## Goals / Non-Goals

**Goals:**

- Add a reviewed local backend wiring path that can run a tiny pilot only when
  every config and environment gate passes.
- Keep `visdoc_retrieve.train_lora_pilot` import-safe in environments without
  optional ML dependencies.
- Enforce `max_steps <= 20`, `sample_limit <= 8`, local model paths only,
  ignored adapter output, final-test exclusion, and no network/model-download
  behavior before training.
- Build the tiny training sample from train hard negatives; use dev inputs only
  for schema/sanity evidence; never read final-test files.
- Emit Phase 5D blocked or pilot evidence with public-safe path redaction and
  no benchmark or improvement claims.

**Non-Goals:**

- Production-grade training, distributed training, full retrieval evaluation,
  LoRA quality optimization, or adapter performance reporting.
- Any HuggingFace/network model resolution or implicit model download.
- Any committed model weights, adapter checkpoints, caches, tensorboard/wandb
  logs, private configs, or final-test metrics.
- Merge, deploy, OpenSpec archive, or README result-claim updates.

## Decisions

1. **Keep gate logic in `training_pilot.py`, isolate backend execution in a new
   module.**
   The existing CLI already writes the evidence contract and has tests for
   blocked behavior. A new `lora_training_backend.py` can expose a narrow
   `run_local_lora_pilot(...)` function while avoiding top-level optional
   imports. Alternative: replace `training_pilot.py` with a trainer class.
   Rejected because that would increase diff size and risk changing existing
   Phase 5B/5C evidence behavior.

2. **Represent optional dependency availability as a gate before backend
   execution.**
   The launcher will check for torch, transformers, peft, and the configured
   visual backend dependency only after all non-import gates pass. Missing
   dependencies produce clear blocked evidence. Alternative: let imports fail
   inside training. Rejected because errors would be less structured and could
   skip evidence generation.

3. **Use `local_files_only=True` and local path validation for model loading.**
   The backend accepts only an existing `local_model_path`; it passes
   local-files-only semantics to transformers when available and never uses a
   remote model identifier as a fetch source. Alternative: allow a model name
   fallback if the local path is missing. Rejected because the phase explicitly
   forbids downloads and model substitution.

4. **Make the tiny pilot best-effort and evidence-first.**
   The backend can run a minimal adapter-producing path when dependencies
   expose the expected APIs; otherwise it blocks with a concrete backend reason.
   It may write adapters only under the ignored adapter output directory when
   `save_adapter=true`; by default committed evidence remains sanitized.
   Alternative: fabricate a mock adapter to prove the path. Rejected because it
   would blur scaffold output with real training.

5. **Treat dev evaluation as schema/sanity only.**
   Phase 5D does not compute final metrics unless a real adapter is produced
   and a future scoped change adds dev evaluation semantics. The dev evidence
   records sample/eval schema and null metrics when blocked. Alternative: reuse
   MVP or mock visual metrics. Rejected because those are not adapter results.

## Risks / Trade-offs

- **Risk: Backend APIs vary across ColPali/ColQwen packages.** -> Mitigation:
  keep backend selection explicit, validate optional module presence, and
  return structured blocked evidence if the configured backend API cannot be
  wired locally.
- **Risk: A tiny pilot loss is misread as retrieval improvement.** ->
  Mitigation: run cards, safety checks, ledger, and human brief state that pilot
  loss is not a benchmark or model-improvement claim.
- **Risk: Private paths leak through reports.** -> Mitigation: committed Phase
  5D reports use local-path summaries and sanitized manifests; private configs
  and raw outputs stay under ignored `.local/`.
- **Risk: Optional imports accidentally move to module import time.** ->
  Mitigation: tests assert top-level import does not load torch, transformers,
  peft, or colpali_engine.
- **Risk: Final-test data is read indirectly.** -> Mitigation: config
  validation rejects final-test paths, backend sample loading reads only train
  hard negatives, and tests monkeypatch path reads to fail on final-test names.
