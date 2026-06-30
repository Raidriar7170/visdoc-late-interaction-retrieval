## Context

VisDoc-Retrieve is through the diagnostic MVP pipeline and optional visual
zero-shot backend scaffold. The committed synthetic smoke corpus has stable
train/dev/test manifests, text baselines, RRF helpers, deterministic mock visual
MaxSim ranking, and explicit final-test boundaries. The next useful checkpoint
is not training; it is a reproducible hard-negative mining surface that prepares
train/dev triples while proving that final test data and positive pages do not
leak into training artifacts.

## Goals / Non-Goals

**Goals:**

- Provide one clean-checkout command for mining:
  `PYTHONPATH=src python -m visdoc_retrieve.mine_hard_negatives --config configs/hard_negatives.json`.
- Use only local committed synthetic smoke manifests and deterministic CPU
  rankers.
- Generate deterministic train/dev hard-negative JSONL records with source,
  rank, score, candidate universe, and evidence fields.
- Combine supported negative sources from existing rankers and metadata:
  BM25, lexical cosine, configured RRF/hybrid text ranking, deterministic mock
  visual MaxSim, same-document wrong pages, and tag-aware negatives.
- Report unsupported or zero-support sources explicitly instead of faking
  support.
- Write summary, leakage-check, run-card, human brief, and progress-ledger
  evidence.

**Non-Goals:**

- LoRA/QLoRA training, adapters, checkpoints, model improvement claims, final
  test evaluation, benchmark result tables, or public superiority claims.
- ColPali/ColQwen/BGE/sentence-transformers downloads or inference.
- GPU/A100 requirements, network access, external embedding services, or
  external caches.
- Replacing the MVP command, changing default MVP mock behavior, or creating a
  RAG/chatbot product surface.

## Decisions

1. Add a dedicated miner module and CLI instead of extending `run_mvp`.
   - Rationale: MVP remains a deterministic diagnostic evidence command. Mining
     writes training-preparation artifacts and deserves a separate command,
     reports directory, and run card.
   - Alternative considered: add a mining flag to `run_mvp`. That would blur the
     existing MVP artifact meaning and make mock visual diagnostics look like
     training data generation.

2. Reuse existing local rankers and metadata rather than introducing embedding
   dependencies.
   - Rationale: BM25, lexical cosine, RRF, and deterministic mock visual MaxSim
     already provide CPU-only hard-negative candidates. Same-document and
     tag-aware candidates can be derived from page/query metadata when support
     exists.
   - Alternative considered: use optional real visual zero-shot scores. That
     would require local model state and could be mistaken for a default real
     visual backend result.

3. Centralize positive/test leakage filtering before records are emitted.
   - Rationale: every source can produce repeated or invalid candidates. A single
     filter/dedupe/order layer keeps `negative_page_id` away from query positives,
     prevents test-split artifacts, and gives stable output bytes.
   - Alternative considered: make each source responsible for leakage filtering.
     That duplicates safety logic and makes future source additions risky.

4. Treat source support as first-class report data.
   - Rationale: some requested sources may have zero support in the tiny synthetic
     corpus. The summary should record `support: 0` or `null` evidence rather
     than silently omitting or fabricating a source.

5. Use JSONL records for triples and JSON/Markdown for review evidence.
   - Rationale: JSONL is append-friendly and round-trippable for future training
     prep, while summary/leakage JSON and a run card are easy to inspect during
     review.

## Risks / Trade-offs

- Hard negatives from tiny synthetic data may look like performance evidence ->
  Mitigation: reports and brief state this is training-preparation smoke data,
  not benchmark improvement.
- Multiple rankers can yield the same wrong page -> Mitigation: deterministic
  dedupe keys preserve one record per query/source/negative and stable ordering.
- Metadata-derived sources may have sparse support -> Mitigation: record support
  counts and unsupported reasons explicitly.
- Future training code may expect fields not present yet -> Mitigation: keep the
  schema minimal but explicit, and test JSONL round-trip behavior.

## Migration Plan

No migration is required. Existing MVP, text, visual-smoke, and optional
visual-zero-shot commands remain unchanged. The new command writes only the
configured hard-negative output paths and updates reviewer evidence.

## Open Questions

- None for this checkpoint. Future real-backend or training use must be scoped in
  a separate accepted OpenSpec change.
