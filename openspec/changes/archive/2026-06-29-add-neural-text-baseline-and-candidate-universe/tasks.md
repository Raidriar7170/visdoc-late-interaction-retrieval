## 1. Contract And Naming Cleanup

- [x] 1.1 Mark this as Phase 2.5 text/candidate-universe clarification, not Phase 4/5 visual-model work.
- [x] 1.2 Rename local `dense_text` to `lexical_cosine` or `local_tfidf_cosine` across code and artifacts.
- [x] 1.3 Keep old metrics diagnostic-only and ensure renamed surfaces do not imply neural embedding execution.

## 2. Candidate Universe Contract

- [x] 2.1 Add candidate universe config parsing for `evaluated_split_pages`, `non_train_pages`, and `all_pages`.
- [x] 2.2 Implement candidate page selection separately from evaluated query split selection.
- [x] 2.3 Add report fields for universe name, candidate counts, evaluated query count, and ranked page support.
- [x] 2.4 Test that current dev-only diagnostics are labeled as `evaluated_split_pages`.
- [x] 2.5 Test that `non_train_pages` and `all_pages` widen candidates without evaluating final-test queries.

## 3. Neural Text Baseline

- [x] 3.1 Add a minimal embedding-provider interface for neural text retrieval.
- [x] 3.2 Implement a deterministic local mock/stub embedding provider for validation and tests.
- [x] 3.3 Add a config-gated neural text retriever that records provider status.
- [x] 3.4 Add BM25+neural RRF as distinct from BM25+lexical RRF.
- [x] 3.5 Test that default validation needs no model download, network, GPU, FAISS, cache, or external path.

## 4. Reports, Docs, And Ledger

- [x] 4.1 Regenerate the text diagnostic report with renamed lexical IDs and candidate-universe metadata.
- [x] 4.2 Update `reports/progress-ledger.yaml` with Phase 2.5 status and unchanged boundary flags.
- [x] 4.3 Update README, AGENTS, configs README, and a concise Chinese Human Brief without result claims.

## 5. Validation

- [x] 5.1 Run `python -m py_compile src/visdoc_retrieve/*.py`.
- [x] 5.2 Parse `pyproject.toml` with `tomllib`.
- [x] 5.3 Run focused tests for candidate universe, lexical rename, and neural-text mock/stub behavior.
- [x] 5.4 Run `pytest -q`, `ruff check .`, `mypy src`, `openspec validate --all --strict`, and `git diff --check`.
- [x] 5.5 Confirm no ColPali/ColQwen, external download, hard negatives, training, final test, new data, or result claims.
