## Context

Phase 5I reached the A100 guarded backend layer with CUDA, the exact local
model path, `torch`, `transformers`, `peft`, and `colpali_engine` available.
The run still blocked on `backend_training_step_unavailable`: the installed
`colpali_engine` exposes model and processor classes such as `ColQwen2` and
`ColQwen2Processor`, but it does not expose the project-specific
`run_visdoc_lora_pilot` hook and its trainer path requires additional
uninstalled dependencies such as `datasets`.

The existing launcher already owns the important safety contract. Phase 5J
should not create another launcher or broaden the training scope. It should add
a reviewed repo-owned backend runner that can execute a tiny optimizer-backed
step only after the existing gates pass, then report a sanitized `pilot_run` or
an exact blocked reason.

## Goals / Non-Goals

**Goals:**

- Add a reviewed backend runner path for `backend_dependency=colpali_engine`
  that uses local-only `transformers.ColQwen2ForRetrieval` or `ColQwen2`,
  `ColQwen2Processor`, `peft`, and `torch` APIs without importing optional ML
  dependencies at module import time.
- Execute only a tiny dev-only pilot after `train_lora_pilot` gates pass:
  `sample_limit <= 8`, `max_steps <= 20`, no final test, no model download, and
  ignored adapter output.
- Return structured backend results that the existing sanitizer can validate:
  `status`, `training_executed`, `effective_training_sample_count`,
  `adapter_checkpoint_created`, `adapter_checkpoint_path`, and
  `final_test_used`.
- Keep blocked outcomes truthful and precise when model loading, processor
  encoding, LoRA wrapping, forward/backward, optimizer stepping, or adapter
  saving cannot safely complete.
- Add focused tests that use fake modules/models/processors so local validation
  does not require CUDA, model downloads, or real A100 weights.

**Non-Goals:**

- Do not add or install dependencies.
- Do not use `colpali_engine.trainer` or `datasets`.
- Do not change hard-negative generation, retrieval metrics, benchmark
  semantics, or final-test behavior.
- Do not commit model weights, adapter checkpoints, caches, local pilot config,
  exact private model paths, or benchmark claims.
- Do not merge, deploy, or archive this change.

## Decisions

1. **Implement a repo-owned reviewed runner branch instead of monkey-patching
   `colpali_engine`.**
   `run_local_lora_pilot` already checks for a third-party
   `run_visdoc_lora_pilot` hook. When that hook is absent and the backend
   dependency is `colpali_engine`, Phase 5J will call a project-owned function
   that imports `ColQwen2`, `ColQwen2Processor`, `peft`, and `torch` lazily.
   This keeps the reviewed behavior under version control and leaves
   third-party packages untouched. Alternative: install or patch an external
   trainer. Rejected because it widens scope and introduces dependency drift.

2. **Load the local ColQwen2 model through `ColQwen2ForRetrieval` first.**
   The A100 model directory is recognized by the installed `transformers` as
   `model_type=colqwen2`, and `transformers` exposes the matching
   `ColQwen2ForRetrieval` / `ColQwen2Processor` classes. Direct
   `colpali_engine.ColQwen2` loading can hit config-shape drift, while generic
   `AutoModel` does not register this retrieval architecture. Phase 5J will
   prefer `ColQwen2ForRetrieval.from_pretrained(..., local_files_only=True)`
   and fall back to `colpali_engine.ColQwen2` only when the transformer-native
   class is unavailable. Alternative: force direct `ColQwen2` construction.
   Rejected because the installed local HF config is already owned by the
   transformer-native retrieval loader.

3. **Use the smallest text-query optimizer-backed probe as the first reviewed
   runner.**
   The runner should load the local ColQwen2 model and processor with
   `local_files_only=True`, wrap the model with LoRA via `peft`, process the
   capped training query texts, compute a scalar tensor from the model output,
   run `backward()`, and perform at most the configured number of optimizer
   steps. This is a tiny pilot proving the optimizer path, not a retrieval
   quality claim. Alternative: build a full query-image contrastive loss.
   Rejected for Phase 5J because image/page materialization and ranking
   evaluation belong to later phases.

4. **Fail closed on any unreviewed or unsafe result.**
   The existing sanitizer already rejects final-test usage, metric/improvement
   fields, excessive sample counts, absolute adapter paths, and adapter output
   mismatches. Phase 5J will keep those checks and add explicit backend blocked
   codes for model load, processor, LoRA wrapping, optimizer step, and adapter
   save failures. Alternative: catch all failures as generic backend errors.
   Rejected because the project uses exact blockers as its truth surface.

5. **Keep evidence public-safe and phase-specific.**
   The A100 run should reuse the Phase 5I/5J local config pattern under
   `local/`, write sanitized Phase 5J evidence under `reports/training-pilot/`,
   and keep adapter outputs under ignored `.local/`. If an adapter is created,
   only the sanitized manifest path is committed; the checkpoint itself remains
   untracked and ignored.

## Risks / Trade-offs

- **The local ColQwen2 processor may require image inputs for real retrieval
  training** -> Phase 5J scopes the runner as a tiny optimizer-backed pilot,
  not a ranking-quality or final retrieval training result.
- **Model loading or LoRA wrapping may still exceed memory or expose API drift**
  -> Return exact blocked evidence and keep no adapter/benchmark claims.
- **A synthetic scalar loss can be misread as a model-improvement result** ->
  Evidence must keep `pilot_loss_reported_as_model_improvement=false`, omit
  metrics, and state final test remains unused.
- **Adapter output leakage** -> Write adapter files only under ignored
  `.local/` and run forbidden artifact scans before commit.
