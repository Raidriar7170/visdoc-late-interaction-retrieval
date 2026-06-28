## 1. Schema And Dependency Setup

- [x] 1.1 Add document-generation dependencies to `pyproject.toml` without adding model, embedding, retrieval, or GPU dependencies.
- [x] 1.2 Add RED tests for page manifest validation, query manifest validation, invalid split/query-type handling, and unknown positive page references.
- [x] 1.3 Implement the minimal data schema/validation module needed to make the schema tests pass.

## 2. Synthetic Corpus Generation

- [x] 2.1 Add RED tests for deterministic default corpus generation with 3 families, 24 pages, and 72 query records.
- [x] 2.2 Implement deterministic technical page specifications covering tables, figures, flow diagrams, specifications, troubleshooting, layout, OCR-failure-style, and mixed Chinese/English signals.
- [x] 2.3 Implement PDF generation and page rendering to local page image artifacts plus OCR-like text artifacts.
- [x] 2.4 Implement deterministic JSONL page/query manifests and corpus summary digests sorted by stable IDs.

## 3. Split And Leakage Validation

- [x] 3.1 Add RED tests for family-consistent train/dev/test splits and query-positive split consistency.
- [x] 3.2 Add RED tests for rejecting training candidate page IDs that include final test pages.
- [x] 3.3 Implement split validation and the validation-only leakage guard without generating hard-negative triples.

## 4. Materialized Smoke Corpus And Documentation

- [x] 4.1 Materialize the default smoke corpus under `data/synthetic-smoke/` using the generator.
- [x] 4.2 Update `data/README.md` with the Phase 1 generated corpus layout and no-result boundary.
- [x] 4.3 Update `reports/progress-ledger.yaml` to record Phase 1 data availability while keeping visual retriever, training, and final test statuses not started.
- [x] 4.4 Replace generated `TBD` Purpose text in the archived Phase 0 main specs with concrete purpose statements.
- [x] 4.5 Generate a concise Chinese Human Brief for Phase 1 under `docs/human-briefs/`.

## 5. Validation And Scope Review

- [x] 5.1 Run `pytest -q` and confirm all tests pass.
- [x] 5.2 Run `ruff check .` and confirm linting passes.
- [x] 5.3 Run `mypy src` and confirm typing passes.
- [x] 5.4 Run `openspec validate --all --strict` and confirm OpenSpec validation passes.
- [x] 5.5 Run `git diff --check` and confirm no whitespace errors.
- [x] 5.6 Review the final file set and text surfaces to confirm Phase 1 did not introduce retrieval models, ranking metrics, embeddings, hard-negative mining outputs, training scripts, adapter checkpoints, benchmark reports, or result claims.
