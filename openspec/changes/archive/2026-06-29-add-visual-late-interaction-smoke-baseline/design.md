## Context

The existing repository has manifest-backed synthetic page images, text
artifacts, query relevance records, deterministic retrieval metrics, and a
config-driven text-baseline report. This phase must add the smallest visual
retrieval smoke layer that can run in local validation while staying clearly
diagnostic.

The visual-smoke retriever is not a replacement for ColPali, ColQwen, or a
real late-interaction model. It is a local guardrail that verifies future visual
retrieval plumbing has a bounded report contract and does not accidentally
require network, GPU, model downloads, training, hard negatives, or final-test
evaluation.

## Decisions

1. Use page image bytes as the only page-side artifact.

   The loader validates Phase 1 page/query manifests and reads `image_path`
   bytes. It records `text_path` metadata but does not open page text artifacts,
   so the report can honestly mark `page_text_artifacts_read: false`.

2. Implement a deterministic hashed patch-token scorer.

   Each image is converted into local patch tokens from lightweight byte-derived
   material. Query tokens and image tokens are embedded with deterministic
   SHA-256-derived vectors, then scored with a late-interaction-style max
   similarity aggregation. This preserves the shape of a visual late-interaction
   smoke test without external models.

3. Keep the report surface parallel to the text-baseline report.

   The report is config-driven, excludes the final test split by default, emits
   retrieval metrics for the dev smoke split, and records diagnostic fields such
   as index size and patch-token support.

4. Keep claims narrow.

   The report and ledger state that this is deterministic local smoke evidence
   only. It does not claim visual-model quality, benchmark improvement, hard
   negative quality, or final-test performance.

## Risks / Trade-offs

- The local hashed scorer is not semantically meaningful visual retrieval.
  Mitigation: name it `visual_smoke`, mark status as `diagnostic_only`, and
  avoid model-quality claims.
- Synthetic image bytes may not contain query-aligned visual content.
  Mitigation: metrics are smoke diagnostics only and final-test remains
  `not_run`.
- The report adds another JSON artifact.
  Mitigation: generate it from config and source code, and keep it within the
  existing report pattern.
