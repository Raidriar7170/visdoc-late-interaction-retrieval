## Why

VisDoc-Retrieve cannot evaluate OCR/text or visual late-interaction retrieval until
page-level data contracts exist. This change creates the Phase 1 data layer:
deterministic synthetic technical documents, rendered page/text artifacts, manifests,
and leakage checks, while keeping retrieval models and benchmark claims out of scope.

## What Changes

- Add schemas and validation utilities for page manifests and query relevance manifests.
- Add a deterministic synthetic technical corpus generator for a small smoke corpus with
  three document families, page-level artifacts, and query-page relevance pairs.
- Add deterministic page rendering outputs and text extraction fixtures suitable for
  future retrieval baselines.
- Add train/dev/test split metadata and checks that prevent final test pages from being
  used by training or future hard-negative mining inputs.
- Add tests for schema validity, deterministic regeneration, content hashing, split
  integrity, and leakage prevention.
- Update progress documentation to record that Phase 1 data format and synthetic corpus
  are available without claiming retrieval results.
- Keep retrieval models, ranking metrics, ColPali/ColQwen inference, embedding caches,
  hard-negative mining, LoRA/QLoRA training, and benchmark result claims out of this
  change.

## Capabilities

### New Capabilities

- `retrieval-data-format`: Defines page manifest, query relevance manifest, source
  metadata, content hashes, split fields, query types, and validation behavior.
- `synthetic-corpus-generation`: Defines deterministic generation of a small visually
  rich technical document corpus and local page/text artifacts.

### Modified Capabilities

- None.

## Impact

- Affected code: new data schema/generation modules under `src/visdoc_retrieve/`,
  focused tests under `tests/`, documentation under `data/`, `reports/`, and the Phase 1
  Human Brief.
- Affected dependencies: lightweight local document/image generation dependencies may be
  added if needed, but no model, embedding, GPU, or retrieval dependency is introduced.
- No runtime retrieval API, ranking implementation, model inference, training script,
  adapter checkpoint, or benchmark report is introduced.
