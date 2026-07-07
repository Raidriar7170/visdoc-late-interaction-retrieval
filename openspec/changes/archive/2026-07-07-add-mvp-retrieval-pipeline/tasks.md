## 1. OpenSpec And Opsx Phase Surfaces

- [x] 1.1 Create proposal, design, tasks, and MVP retrieval pipeline spec.
- [x] 1.2 Add or update `.opsx-goal.yaml` for the bounded MVP goal.
- [x] 1.3 Add `.opsx-auto-inbox/` phase manifests with scope, files, validation,
  evidence, and completion/impossibility fields.
- [x] 1.4 Validate the OpenSpec change with strict validation.

## 2. Tests First

- [x] 2.1 Add RED tests for MaxSim correctness, shape validation, empty token
  handling, deterministic mock visual embeddings, and cache round-trip.
- [x] 2.2 Add RED tests for tiny-fixture retrieval ranking and shared candidate
  universe boundaries.
- [x] 2.3 Add RED tests for MVP pipeline smoke execution, required artifacts,
  metrics, rankings, run-card boundaries, human brief existence, and ledger YAML
  parsing.

## 3. Visual Mock Scaffold

- [x] 3.1 Add `VisualRetriever` protocol and deterministic
  `MockVisualRetriever` while preserving existing visual-smoke behavior.
- [x] 3.2 Add public MaxSim scoring and embedding shape validation.
- [x] 3.3 Add deterministic JSON cache schema, writer, loader, and round-trip
  checks for mock query/page token embeddings.

## 4. MVP Pipeline

- [x] 4.1 Add `configs/mvp.json` with fixed synthetic smoke manifests, `dev`
  evaluated split, `evaluated_split_pages` candidate universe, text methods,
  visual mock method, and output paths.
- [x] 4.2 Add the `visdoc_retrieve.run_mvp` module entry point and pipeline
  orchestration.
- [x] 4.3 Emit `reports/mvp/metrics.json`, `reports/mvp/rankings.csv`, visual
  cache evidence, and `reports/mvp/run-card.md`.
- [x] 4.4 Compute overall and query-type subset metrics with `support: 0` and
  `metrics: null` for missing subsets.

## 5. Documentation And Evidence

- [x] 5.1 Update README/config docs with the MVP command and diagnostic-only
  boundaries.
- [x] 5.2 Update `reports/progress-ledger.yaml` with an MVP entry and evidence
  paths.
- [x] 5.3 Generate a concise Chinese/English human brief under
  `docs/human-briefs/`.

## 6. Validation And Review

- [x] 6.1 Run required focused and full validation commands, including the MVP
  smoke command and artifact existence checks.
- [x] 6.2 Run a Reviewer subagent over the diff and fix any Must Fix items.
- [x] 6.3 Record final phase evidence and stop without commit, push, merge,
  deploy, or archive.
