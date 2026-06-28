## 1. Project Metadata And Package Skeleton

- [x] 1.1 Create `pyproject.toml` with package metadata and committed pytest, Ruff, and mypy configuration.
- [x] 1.2 Create the minimal `src/visdoc_retrieve/` package structure without retrieval, data, model, training, or evaluation modules.
- [x] 1.3 Add a local-only smoke test under `tests/` that verifies the package imports without data files, network access, GPU hardware, or model downloads.

## 2. Documentation And Project State

- [x] 2.1 Create `README.md` with first-screen algorithmic positioning, explicit no-final-results wording, and no unsupported benchmark claims.
- [x] 2.2 Create repository `AGENTS.md` with Phase 0 scope boundaries and future OpenSpec workflow expectations.
- [x] 2.3 Create placeholder `configs/`, `reports/`, and `data/README.md` surfaces without data generation, retrieval implementation, metrics, or model configuration.
- [x] 2.4 Initialize a bounded progress ledger under `reports/` with Phase 0 state and not-started statuses for data, visual retrieval, training, and final testing.

## 3. Validation And Closeout

- [x] 3.1 Run `pytest -q` and confirm the smoke validation passes locally.
- [x] 3.2 Run `ruff check .` and confirm linting passes.
- [x] 3.3 Run `mypy src` and confirm typing passes.
- [x] 3.4 Run `openspec validate --all --strict` and confirm OpenSpec validation passes.
- [x] 3.5 Review the final diff to confirm Phase 0 did not introduce future-phase data generation, retrievers, metrics, model inference, training, adapter checkpoints, or benchmark reports.
- [x] 3.6 If the apply phase is treated as non-trivial, generate a concise Chinese Human Brief under `docs/human-briefs/` from the accepted artifacts and validation output.
