## Why

Phase 5H closed the A100 model-path gate with static marker evidence, but the
project still lacks a truthful Phase 5I checkpoint that actually attempts one
tiny gated real LoRA / QLoRA pilot on the A100 runtime. This phase should
attempt that pilot with a very small budget and commit only sanitized
metadata, whether the run succeeds or blocks.

## What Changes

- Add a Phase 5I checkpoint that starts from clean `origin/main` in a dedicated
  branch/worktree, prepares an untracked local pilot config, and attempts one
  tiny A100 pilot only when every existing real-training gate is satisfied.
- Parameterize `train_lora_pilot` public evidence metadata so Phase 5I can emit
  its own schema IDs, titles, run-card names, and progress-ledger section while
  preserving Phase 5D defaults.
- Ignore `local/` so the untracked Phase 5I private config cannot be committed.
- Refresh repo-local `opsx-auto practical` path inputs so the new Phase 5I
  OpenSpec change and goal/phase files are admitted by the guarded runtime.
- Commit only sanitized Phase 5I environment, safety, run-card, adapter
  manifest, dev-eval, Human Brief, and progress-ledger evidence; if the pilot
  blocks, commit blocked evidence instead of faking success.
- Do not download models, use network for model resolution, run final test,
  claim benchmark improvement, commit model weights/adapters/caches/private
  config/private model path, merge, deploy, or archive this change.

## Capabilities

### New Capabilities

- `gated-tiny-real-pilot-attempt`: Defines the Phase 5I A100 gated tiny real
  pilot attempt or truthful blocked checkpoint, phase-specific sanitized
  evidence, and no-claim/no-artifact boundaries.

### Modified Capabilities

None.

## Impact

- Updates `src/visdoc_retrieve/training_pilot.py` and
  `src/visdoc_retrieve/train_lora_pilot.py` to support phase-specific public
  metadata without changing the guarded training logic.
- Updates `.gitignore` and focused tests for `local/` private config handling
  and Phase 5I metadata/report behavior.
- Adds Phase 5I OpenSpec artifacts, `opsx-auto` practical goal/phase inputs,
  sanitized `reports/training-pilot/` evidence, a concise Chinese Human Brief,
  and a Phase 5I progress-ledger entry.
- Does not add feature work beyond the gated pilot attempt, does not change
  retrieval metrics, and does not widen the repository into merge, deploy, or
  benchmark-claim work.
