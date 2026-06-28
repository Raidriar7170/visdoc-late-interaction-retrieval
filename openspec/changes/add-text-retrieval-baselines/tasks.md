## 1. Corpus Loader And Config

- [x] 1.1 Add RED tests for loading Phase 1 page/query manifests plus text artifacts into a split-aware text retrieval corpus.
- [x] 1.2 Add RED tests that missing page text artifacts fail fast instead of indexing empty content.
- [x] 1.3 Implement the manifest-backed text corpus loader using existing Phase 1 validators and repo-relative path resolution.
- [x] 1.4 Add a committed default config for synthetic-smoke text baselines that enables BM25, dense-text, and hybrid/RRF while excluding the final test split.

## 2. Text Retrieval Baselines

- [x] 2.1 Add RED toy tests for BM25 lexical ranking and stable page-ID tie-breaking.
- [x] 2.2 Implement deterministic tokenization and the internal BM25 retriever.
- [x] 2.3 Add RED toy tests for the default dense-text baseline running without network, GPU, external model downloads, or FAISS.
- [x] 2.4 Implement the deterministic local dense-text baseline and keep optional external embedding paths disabled by default.
- [x] 2.5 Add RED toy tests for reciprocal-rank fusion and hybrid tie-breaking.
- [x] 2.6 Implement the hybrid/RRF retriever over BM25 and dense-text rankings.

## 3. Metrics And Report Generation

- [x] 3.1 Add RED metric tests for Recall@1, Recall@5, MRR, and NDCG@10 using toy rankings with known positive positions.
- [x] 3.2 Implement retrieval metric computation with evaluated-query and ranked-page support counts.
- [x] 3.3 Add RED tests for report generation from config, including method sections, diagnostic latency/index-size fields, hard-negative `not_available` status, and final-test `not_run` status.
- [x] 3.4 Implement the config-driven report runner and a local command entry point for generating the text-baseline report.
- [x] 3.5 Generate deterministic diagnostic report artifacts under `reports/` from the synthetic-smoke config.

## 4. Documentation And Progress Surfaces

- [x] 4.1 Update `reports/progress-ledger.yaml` to record Phase 2 text baseline status while keeping visual retrieval, training, and final test statuses unstarted or not run.
- [x] 4.2 Update `README.md`, `configs/README.md`, or `data/README.md` only as needed to document the text-baseline command and diagnostic-only boundary.
- [x] 4.3 Generate a concise Chinese Human Brief for Phase 2 under `docs/human-briefs/`.
- [x] 4.4 Review text surfaces to ensure they do not claim ColPali/ColQwen results, adapter improvements, hard-negative mining, or final benchmark performance.

## 5. Validation And Review

- [x] 5.1 Run `pytest -q` and confirm all tests pass.
- [x] 5.2 Run `ruff check .` and confirm linting passes.
- [x] 5.3 Run `mypy src` and confirm typing passes.
- [x] 5.4 Run `openspec validate --all --strict` and confirm OpenSpec validation passes.
- [x] 5.5 Run `git diff --check` and confirm no whitespace errors.
- [x] 5.6 Run a scope scan for forbidden Phase 2 expansions: visual inference, model downloads required by validation, GPU/A100 dependency, hard-negative triple output, training artifacts, final test metric claims, and improvement claims.
