## Why

Phase 5B added a guarded launch gate for a future real LoRA / QLoRA pilot, but
the project still needs a Phase 5C execution checkpoint that attempts the tiny
pilot on an A100/local-model environment and records only public-safe evidence.
This phase should truthfully distinguish a real pilot run from a blocked run
without widening into benchmark claims or committing training artifacts.

## What Changes

- Add a Phase 5C checkpoint that uses the existing hard-negative inputs and
  `visdoc_retrieve.train_lora_pilot` launch gate with explicit real-training
  permission, final-test disabled, a tiny budget, and ignored adapter output.
- Use a local-only untracked pilot config for private path values, or a
  sanitized committed config if a public reproduction surface is needed, while
  never committing the true local model path.
- Attempt the tiny pilot only when the private local model path, CUDA/GPU,
  environment variable, adapter-output ignore rule, budget, and dev-only run
  card gates are all satisfied.
- If the pilot is blocked, record a blocked run-card and structured evidence
  with the exact missing prerequisite instead of forcing or faking success.
- Commit only sanitized Phase 5C evidence: environment check, safety check,
  run card, sanitized adapter manifest, dev-eval schema or dev-eval record,
  human brief, and progress-ledger entry.
- Do not download models, use network access for model resolution, run final
  test data, claim benchmark improvement, commit model weights/adapters/
  checkpoints/caches/logs, merge, deploy, or archive OpenSpec.

## Capabilities

### New Capabilities

- `training-pilot-execution-checkpoint`: Defines Phase 5C real-pilot execution
  or blocked evidence, sanitized report artifacts, private-path redaction,
  final-test exclusion, and no-claim/no-artifact-commit boundaries.

### Modified Capabilities

None.

## Impact

- Adds OpenSpec artifacts for the Phase 5C checkpoint.
- Adds sanitized committed evidence under `reports/training-pilot/`, a concise
  Chinese human brief under `docs/human-briefs/`, and a Phase 5C progress-ledger
  entry.
- May add or adjust ignore rules only if a local adapter/checkpoint/cache/log
  path is not already ignored.
- Preserves the existing MVP pipeline, optional visual zero-shot scaffold,
  hard-negative mining outputs, Phase 5A readiness dry run, and Phase 5B launch
  gate claims.
