## Context

Phase 2 added text-only diagnostics over the synthetic smoke `dev` split. The
current report ranks 24 dev queries over 8 dev pages and records those metrics
as diagnostic-only. That is useful for smoke validation, but it leaves two
review questions open:

- whether a retrieval run searched only the evaluated split, all pages, or a
  non-train candidate pool;
- whether `dense_text` means a real neural embedding model or the current local
  lexical-vector cosine baseline.

Phase 3A added only a deterministic local visual-smoke baseline. This Phase
2.5 proposal stays before real ColPali/ColQwen work and keeps the project on
local CPU validation.

## Goals / Non-Goals

**Goals:**

- Make the current text baseline naming honest by replacing `dense_text` with
  a lexical cosine / local TF-IDF cosine name.
- Add explicit candidate universe configuration and report fields so every
  metric is tied to its candidate pool.
- Add a neural text baseline interface that can represent BGE-M3 or
  sentence-transformers later, while tests and default validation use a mock or
  deterministic local embedding provider.
- Add BM25+neural RRF as a separate hybrid from BM25+lexical RRF.
- Preserve Phase 3A boundaries in docs, reports, and ledgers.

**Non-Goals:**

- No ColPali/ColQwen inference or image embedding pipeline.
- No external embedding download or network requirement in default validation.
- No new data, generated pages, queries, hard-negative triples, adapters,
  checkpoints, training scripts, or embedding caches.
- No final test query evaluation and no benchmark result claim.
- No README claim that any baseline improved retrieval quality.

## Decisions

1. Keep candidate universe separate from evaluated query split.

   Evaluated queries remain a split selector such as `dev`. Candidate universe
   is a separate config field with explicit values:
   `evaluated_split_pages`, `non_train_pages`, and `all_pages`. The current
   Phase 2 behavior maps to `evaluated_split_pages`; broader pools can be
   enabled without changing query split semantics.

2. Treat test pages as candidates only when explicitly configured, not as final
   test evaluation.

   A `non_train_pages` run may rank dev queries against dev+test page
   candidates, but it still records `final_test_status: not_run` because test
   queries and final benchmark scoring are not evaluated. Reports must state
   candidate families/pages separately from evaluated query support.

3. Rename local `dense_text` rather than pretending it is neural.

   The existing implementation is deterministic lexical cosine over local text
   tokens. It should become `lexical_cosine` or `local_tfidf_cosine` in public
   surfaces. Backward compatibility can be handled by a small migration in
   configs/tests, not by keeping the misleading method label.

4. Add neural text as a provider interface with a local mock/stub default.

   The neural retriever should accept an embedding provider abstraction. The
   default test provider is deterministic and local. Real BGE-M3 or
   sentence-transformers execution remains config-gated, disabled by default,
   and outside this phase unless a later accepted change enables model assets
   and cache policy.

5. Keep hybrid names explicit.

   BM25+lexical RRF and BM25+neural RRF must be separate method IDs so report
   readers can tell which dense side was used. This prevents a future
   BM25+neural result from being compared against the older local cosine
   hybrid without context.

## Risks / Trade-offs

- Renaming `dense_text` can break local references to older report fields.
  Mitigation: update config, report, tests, docs, and ledger in one bounded
  pass; do not keep duplicate public names unless a compatibility note is
  needed in archived artifacts.
- Candidate universe expansion can change metric values without changing the
  model. Mitigation: every report records universe type, candidate page count,
  candidate split counts, and evaluated query count.
- A mock neural provider can be mistaken for real model evidence. Mitigation:
  report provider type, `external_embeddings_enabled: false`, and
  `neural_text_status: mock_or_local_stub` when no real provider is enabled.
- Ranking dev queries against test pages could look like final-test use.
  Mitigation: only candidate pages may be included; final test query evaluation
  remains blocked and explicitly recorded as `not_run`.
- Adding a provider interface before real models creates some scaffolding.
  Mitigation: keep it minimal, local, and testable; no cache directory, model
  dependency, or download path is required in this phase.
