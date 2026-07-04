## Context

Phase 5G established that the A100 checkout, allowed-root runtime placement,
optional dependency importability, CUDA visibility, and idle-GPU observation can
all be checked without launching a real-training job. Its remaining blocker was
the exact A100-side model path. The model directory has since been placed under
the allowed root, but this phase is still a gate closure step, not a training
pilot.

The existing `a100_preflight` helper already produces redacted evidence,
truthful ready/blocked statuses, and safety flags for Phases 5E through 5G.
Phase 5H should extend that helper rather than introducing a second reporting
surface.

## Goals / Non-Goals

**Goals:**

- Verify the exact A100-side model path by static directory and marker checks.
- Treat config, weight, and processor/tokenizer markers as the minimum model
  path readiness signal for this gate.
- Inherit Phase 5G dependency/runtime/CUDA safety gates and report
  `runtime_ready` only when every gate is ready.
- Keep committed JSON, run-card, ledger, and Human Brief evidence public-safe
  by redacting the exact private model path.

**Non-Goals:**

- Do not run `train_lora_pilot` or any training workload.
- Do not load the model, instantiate processors, or call `from_pretrained`.
- Do not download, resolve, or synthesize model weights.
- Do not create adapters, checkpoints, training caches, final-test metrics, or
  benchmark tables.
- Do not scan unrelated model directories to infer readiness.

## Decisions

1. **Build Phase 5H on top of Phase 5G evidence.** Phase 5H should reuse the
   established remote checkout, dependency, CUDA, allowed-root, and safety
   calculations, then add only the exact model-path marker closure fields.

2. **Use static marker verification.** The model path gate closes when the
   structured A100 observation says the directory exists under the allowed
   root, is readable by the checked runtime, and has the required config,
   weight, and processor/tokenizer markers. This avoids model loading while
   still providing a concrete readiness signal.

3. **Fail closed on path placement and markers.** Missing paths, outside-root
   paths, unreadable paths, and missing markers remain blocked outcomes. Missing
   path still requires user input; malformed or outside-root paths are reported
   as blockers without expanding this phase into download or relocation.

4. **Keep runtime-ready separate from execution-ready.** A `runtime_ready`
   Phase 5H status means pre-training gates are closed. It does not mean
   training ran, adapters were created, final-test evaluation happened, or
   retrieval improved.

## Risks / Trade-offs

- **Marker checks are not full model validation** -> explicitly label the
  verification mode as static markers only and keep model loading out of scope.
- **Committed evidence could expose private paths** -> store only redacted path
  location and `exact_path_committed=false`; safety scans must cover Phase 5H
  reports and Human Brief.
- **GPU state may drift before a later pilot** -> record Phase 5H as a fresh
  pre-training gate snapshot only; a later real-pilot phase must re-check GPU
  placement before launching.
- **Runtime-ready language can overclaim** -> keep safety flags false and state
  that the next step is a separate gated pilot attempt, not an implied training
  success.
