## Why

Phase 2 text-only baselines are archived, but the project still lacks any
local visual retrieval smoke path. The next phase needs a tiny diagnostic
visual baseline that exercises page-image loading, late-interaction-style
ranking, report generation, and boundary evidence without introducing model
downloads, GPU requirements, training, hard-negative mining, final-test
evaluation, or benchmark claims.

## What Changes

- Add a deterministic local visual-smoke retriever over manifest-backed page
  image artifacts.
- Add a config-driven visual-baseline smoke report for the synthetic smoke dev
  split.
- Add tests for image-artifact loading, deterministic ranking, report shape,
  final-test exclusion, and diagnostic-only boundary flags.
- Add a visual retrieval baseline spec and concise Chinese Human Brief.
- Update the progress ledger with honest visual-smoke status and non-goals.

## Non-Goals

- No ColPali/ColQwen model inference.
- No external model download, network dependency, GPU/A100 dependency, or FAISS.
- No hard-negative mining output.
- No LoRA/QLoRA training, adapters, checkpoints, or model improvement claim.
- No final-test evaluation or public benchmark result.
- No chatbot UI, generic RAG app, deployment, merge, push, or release.

## Capabilities

### New Capabilities

- `visual-retrieval-baselines`: Deterministic local visual-smoke retrieval and
  diagnostic reporting over synthetic smoke page images.

### Modified Capabilities

- None.

## Impact

- Affected files: `src/visdoc_retrieve/`, `tests/`, `configs/`, `reports/`,
  `openspec/changes/add-visual-late-interaction-smoke-baseline/`,
  `docs/human-briefs/`, and `reports/progress-ledger.yaml`.
- Validation remains local-only through `scripts/validate-local-core.sh`.
