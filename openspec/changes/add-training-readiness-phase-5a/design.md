## Context

Phase 5A follows three validated diagnostic layers: the MVP retrieval pipeline,
the optional local visual zero-shot backend scaffold, and Phase 4
hard-negative mining. Those layers provide deterministic local artifacts but
do not yet provide a training-preparation package that freezes inputs,
validates triples, records safety boundaries, and proves that a future training
phase can start without touching final test data or performing real model
work.

## Goals / Non-Goals

**Goals:**

- Add a local-only readiness package that validates train/dev hard-negative
  JSONL artifacts and converts them into deterministic triples.
- Freeze hashes for hard negatives, corpus, query, and qrels-style relevance
  inputs alongside candidate-universe and split policy metadata.
- Provide a CPU-safe mock scorer/loss smoke test that exercises ranking-loss
  semantics without requiring torch or model libraries.
- Provide a dry-run trainer entry point that performs parsing, hashing,
  loading, leakage checks, mock batch construction, mock loss computation, and
  report generation.
- Record explicit safety evidence that no training, model download, GPU run,
  final-test evaluation, adapter checkpoint, model weights, or benchmark claim
  were produced.

**Non-Goals:**

- Real ColPali, ColQwen, BGE, sentence-transformers, or adapter training.
- A100 execution, GPU scheduling, torch/transformers import requirements, or
  model downloads.
- Final test evaluation, benchmark tables, retrieval-improvement claims, or
  model-superiority claims.
- Changing existing MVP metrics/reports, optional visual zero-shot semantics,
  or hard-negative mining output semantics.

## Decisions

1. **Use committed local JSON configs instead of implicit CLI defaults.**
   `configs/train_lora_dry_run.json` is the default deterministic dry run,
   while `configs/train_lora.local.example.json` documents the future local
   model-path fields without enabling training. This keeps every readiness
   decision inspectable and testable.

2. **Treat Phase 4 JSONL files as immutable training-readiness inputs.**
   The loader reads `data/derived/hard_negatives/train.jsonl` and
   `data/derived/hard_negatives/dev.jsonl`, validates the Phase 4 schema,
   checks split/candidate-universe consistency against the config, rejects
   positive/negative collisions, and emits triples in deterministic input
   order with an optional deterministic dry-run sample limit.

3. **Use standard-library-only mock loss by default.**
   The loss smoke surface uses deterministic fake embeddings and a simple
   pairwise margin/ranking loss. Torch remains optional and unimported by
   default, so local validation stays CPU-only and dependency-light.

4. **Generate report artifacts from the dry-run command, not by hand.**
   The CLI writes `artifact-freeze.json`, `dataset-summary.json`,
   `dry-run-card.md`, and `safety-check.json` from parsed config, file hashes,
   loaded triples, and computed mock loss. The human brief summarizes those
   artifacts and points back to them rather than becoming a second source of
   truth.

5. **Fail closed on safety-sensitive flags.**
   `allow_final_test` defaults false and any true value is rejected in Phase 5A.
   `dry_run` must be true for the current CLI. A configured local model path
   can be checked for presence but must not trigger training, checkpoint
   creation, model loading, or downloads.

## Risks / Trade-offs

- **Risk: Dry-run artifacts are mistaken for model performance.** Mitigation:
  reports and safety checks state that mock loss and mock batches are not
  training results or benchmark evidence.
- **Risk: Loader accepts split leakage from malformed artifacts.** Mitigation:
  loader validates query/page split boundaries from manifests and rejects test
  split use in train/dev readiness outputs.
- **Risk: Optional future model fields invite accidental training.** Mitigation:
  dry-run CLI rejects non-dry-run configs and writes no adapter checkpoint even
  when `local_model_path` is populated.
- **Risk: Report timestamps make outputs nondeterministic.** Mitigation:
  use a deterministic configured/report timestamp for committed dry-run
  artifacts and test hash stability independently from wall-clock time.
