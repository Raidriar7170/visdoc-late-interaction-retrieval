## Why

Phase 5A proves the training inputs can be frozen and dry-run locally, but the
project still lacks a guarded handoff into a real LoRA / QLoRA visual retriever
pilot. This change adds the Phase 5B launch gate so a future pilot can start
only when local model weights, CUDA, explicit config permission, and a tiny
budget are all present, while default local validation remains blocked,
CPU-safe, and dependency-light.

## What Changes

- Add a local-only pilot config example for real visual retriever adaptation
  with explicit model identity, local model path, adapter output, hard-negative
  inputs, dev-only evaluation inputs, loss/hyperparameter/budget fields, and
  training/final-test safety flags.
- Add a `visdoc_retrieve.train_lora_pilot` CLI that performs config validation
  and environment checks by default, exits clearly with blocked evidence when a
  gate is unmet, and enters real pilot training only if every safety gate is
  satisfied.
- Add an import-safe training launcher scaffold whose optional torch,
  transformers, peft, and ColPali/ColQwen imports live only behind the guarded
  real-training path.
- Add dev-only evaluation and adapter-manifest schemas that can record
  not-run/null-metric status without fabricating adapter performance or
  improvement claims.
- Add deterministic Phase 5B report artifacts, a concise Chinese human brief,
  progress-ledger entry, and tests covering gate behavior, import safety,
  blocked run-card generation, ignore rules, and preservation of existing CLIs.
- Do not download model weights, use network access, run final test data, claim
  benchmark improvement, commit model weights/adapters/checkpoints, or convert
  the project into a RAG chatbot.

## Capabilities

### New Capabilities

- `training-pilot-launch-gate`: Defines the Phase 5B local-only real-training
  pilot gate, blocked evidence behavior, guarded optional imports, dev-only
  evaluation schema, adapter manifest schema, and no-final-test/no-claim
  boundaries.

### Modified Capabilities

None.

## Impact

- Adds `configs/train_lora_pilot.local.example.json`.
- Adds Python modules and CLI entry point under `src/visdoc_retrieve/` for
  pilot config parsing, gate checks, blocked/pilot run-card output, dev-only
  evaluation schema output, adapter manifest example output, and guarded real
  launcher scaffolding.
- Adds tests for Phase 5B behavior plus regression coverage for MVP,
  hard-negative mining, Phase 5A dry-run, and optional dependency import
  boundaries.
- Updates `.gitignore`, `reports/progress-ledger.yaml`, deterministic
  `reports/training-pilot/` artifacts, and `docs/human-briefs/`.
