## 1. OpenSpec Artifacts

- [x] 1.1 Add proposal, design, tasks, and visual-retrieval-baselines spec delta.
- [x] 1.2 Validate the change with OpenSpec strict validation.

## 2. Visual Smoke Retrieval

- [x] 2.1 Add RED tests for visual corpus loading, missing image failure, and deterministic visual-smoke ranking.
- [x] 2.2 Implement manifest-backed visual corpus loading from page image artifacts only.
- [x] 2.3 Implement deterministic local visual-smoke late-interaction ranking with stable page-ID tie-breaking.

## 3. Visual Smoke Report

- [x] 3.1 Add RED tests for config-driven visual report generation and diagnostic boundary flags.
- [x] 3.2 Add committed visual-baseline smoke config.
- [x] 3.3 Implement report generation and materialize the synthetic smoke report.

## 4. Evidence And Documentation

- [x] 4.1 Update the progress ledger with diagnostic visual-smoke status.
- [x] 4.2 Generate a concise Chinese Human Brief under `docs/human-briefs/`.

## 5. Validation

- [x] 5.1 Run focused visual retrieval/report tests.
- [x] 5.2 Run `scripts/validate-local-core.sh`.
- [x] 5.3 Run `openspec validate --all --strict`.
- [x] 5.4 Run `git diff --check`.
- [x] 5.5 Confirm no model download, GPU dependency, training, hard-negative output, final-test evaluation, benchmark claim, staging, merge, push, or external review is introduced.
