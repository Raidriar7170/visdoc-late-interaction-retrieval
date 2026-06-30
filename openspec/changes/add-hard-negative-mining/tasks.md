## 1. OpenSpec Phase Surface

- [x] 1.1 Create proposal, design, tasks, and hard-negative mining spec.
- [x] 1.2 Validate the new OpenSpec change with strict validation.

## 2. Tests First

- [x] 2.1 Add RED tests for hard-negative record schema round-trip, deterministic
  dedupe, stable ordering, and required fields.
- [x] 2.2 Add RED tests for split leakage checks: no positive-as-negative, no
  dev/test query leakage into train triples, no test query leakage into dev
  triples, and no test split in training artifacts.
- [x] 2.3 Add RED tests for configured source reporting: BM25, lexical cosine,
  available RRF/hybrid, deterministic mock visual MaxSim, same-document,
  tag-aware, and unsupported/zero-support sources.
- [x] 2.4 Add RED tests for the CLI/config outputs, run-card boundaries, human
  brief existence, progress-ledger parsing, and unchanged MVP execution.

## 3. Miner Implementation

- [x] 3.1 Add `configs/hard_negatives.json` with train/dev evaluated splits,
  explicit candidate universe, local-only sources, top-k limits, and output
  paths.
- [x] 3.2 Add hard-negative config dataclasses/loading, path validation, and
  final-test split rejection.
- [x] 3.3 Add hard-negative record schema, JSONL writer/loader, deterministic
  dedupe, and ordering utilities.
- [x] 3.4 Add source candidate generation from BM25, lexical cosine, available
  RRF/hybrid text ranking, deterministic mock visual MaxSim, same-document wrong
  pages, and tag-aware metadata when supported.
- [x] 3.5 Add central leakage checks and summary support accounting with
  unsupported/zero-support reporting.
- [x] 3.6 Add `visdoc_retrieve.mine_hard_negatives` CLI orchestration.

## 4. Evidence Outputs

- [x] 4.1 Emit train/dev JSONL triples under `data/derived/hard_negatives/`.
- [x] 4.2 Emit `reports/hard-negatives/mining-summary.json`,
  `reports/hard-negatives/leakage-check.json`, and
  `reports/hard-negatives/run-card.md`.
- [x] 4.3 Generate a concise Chinese human brief under `docs/human-briefs/`.
- [x] 4.4 Update `reports/progress-ledger.yaml` with a hard-negative mining
  checkpoint entry and no training/final-test/improvement claims.

## 5. Validation And Review

- [x] 5.1 Run the required MVP smoke, mining CLI, py_compile, pyproject parse,
  pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check`.
- [x] 5.2 Run a Reviewer subagent over the diff and fix Must Fix items only.
- [ ] 5.3 Commit, push `codex/add-hard-negative-mining`, create a PR, and stop
  without merge, deploy, or OpenSpec archive.
