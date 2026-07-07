## Why

The MVP pipeline now gives deterministic mock visual smoke evidence, but the
project still lacks a safe, reproducible entry point for users who already have
local ColPali / ColQwen-style visual-model weights. This change adds the
minimum real-backend boundary needed to exercise visual zero-shot retrieval
locally without changing default CI, default tests, default MVP artifacts, or
diagnostic-only claims.

## What Changes

- Add a config-gated optional visual zero-shot backend surface with a real
  local-model adapter scaffold and clear missing-model errors.
- Keep `MockVisualRetriever` deterministic and default for the MVP pipeline.
- Add an example local config at
  `configs/visual_zero_shot.local.example.json` that is not required by CI.
- Add an optional CLI,
  `PYTHONPATH=src python -m visdoc_retrieve.run_visual_zero_shot --config configs/visual_zero_shot.local.example.json`,
  with `--check-config` / `--dry-run` support.
- Add tests for config parsing, missing local model handling, import safety,
  deterministic mock behavior, MaxSim, real-cache schema compatibility, and
  unchanged MVP execution.
- Add a concise Chinese human brief and progress-ledger checkpoint entry that
  preserve the no-training, no-hard-negatives, no-final-benchmark boundary.

## Capabilities

### New Capabilities

- `visual-zero-shot-backend`: Optional config-gated real visual late-interaction
  backend adapter and local smoke entry point for user-provided local model
  weights.

### Modified Capabilities

- `visual-retrieval-baselines`: Clarify that deterministic mock visual
  retrieval remains the default and that optional real visual zero-shot
  execution is a separate local-only backend path.

## Impact

- Affected code: `src/visdoc_retrieve/` visual backend/config/CLI modules and
  focused tests.
- Affected artifacts: `configs/visual_zero_shot.local.example.json`,
  `docs/human-briefs/2026-06-30-visual-zero-shot-backend.html`, and
  `reports/progress-ledger.yaml`.
- No new default dependency, network access, model download, GPU requirement,
  A100 use, hard-negative mining, LoRA/QLoRA training, final-test evaluation,
  chatbot/RAG app behavior, deployment, or benchmark-improvement claim is
  introduced.
