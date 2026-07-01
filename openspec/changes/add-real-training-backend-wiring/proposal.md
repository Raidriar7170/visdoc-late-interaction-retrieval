## Why

Phase 5C truthfully proved that the current pilot launcher is still
scaffold-only after the real-training gates. Phase 5D wires an optional,
local-only real LoRA / QLoRA pilot backend behind the same gates so a tiny
pilot can run only when every prerequisite is present, while default validation
continues to block safely.

## What Changes

- Add a Phase 5D real-training backend module that is import-safe at top level
  and imports torch, transformers, peft, and the selected visual backend only
  inside the guarded real-training function.
- Extend the existing `train_lora_pilot` launcher to enforce
  `allow_real_training=true`, `allow_final_test=false`,
  `VISDOC_ENABLE_REAL_TRAINING=1`, local model path existence, CUDA
  availability, optional dependency availability, `max_steps <= 20`,
  `sample_limit <= 8`, ignored adapter output, and pilot/dev-only/not-final
  run-card wording before attempting a tiny backend run.
- Add `sample_limit`, real-backend selection, and safe adapter-output behavior
  to the local example config while keeping the committed example blocked by
  default and free of private model paths.
- Generate Phase 5D environment, safety, run-card, sanitized adapter manifest,
  and dev-eval schema/report evidence for either a blocked run or a tiny
  pilot, without committing adapters, weights, caches, private paths, or final
  test metrics.
- Add focused tests for the new gates, optional import boundaries, blocked
  evidence, sample limiting, final-test exclusion, and preservation of existing
  MVP, hard-negative, Phase 5A, Phase 5B, and Phase 5C behavior.
- Do not download models, use network access for model resolution, run final
  test data, claim benchmark improvement, report pilot loss as model
  improvement, merge, deploy, or archive OpenSpec.

## Capabilities

### New Capabilities

- `real-training-backend-wiring`: Defines the Phase 5D optional local-only
  real LoRA / QLoRA pilot backend wiring, strict gate behavior, sample-limit
  enforcement, sanitized evidence, and no-final-test/no-claim boundaries.

### Modified Capabilities

None.

## Impact

- Adds or updates training pilot code under `src/visdoc_retrieve/`, including a
  real-backend wiring module and the existing `train_lora_pilot` gate.
- Updates `configs/train_lora_pilot.local.example.json`.
- Adds Phase 5D report artifacts under `reports/training-pilot/`, a concise
  Chinese human brief under `docs/human-briefs/`, and a Phase 5D
  `reports/progress-ledger.yaml` entry.
- May update `.gitignore` only if needed to keep adapter outputs, checkpoints,
  model weights, training caches, tensorboard logs, and wandb logs out of Git.
- Preserves the deterministic MVP pipeline, optional visual zero-shot scaffold,
  hard-negative mining, Phase 5A readiness dry run, Phase 5B launch gate, and
  Phase 5C blocked pilot evidence without changing their claims.
