## 1. OpenSpec Phase Surface

- [x] 1.1 Create proposal, design, specs, and tasks for Phase 5A training readiness.
- [x] 1.2 Validate the new OpenSpec change with strict validation before implementation.

## 2. Tests First

- [x] 2.1 Add RED tests for dry-run config parsing, required fields, `dry_run=true`, and `allow_final_test=false` rejection.
- [x] 2.2 Add RED tests for train/dev hard-negative schema loading, split leakage rejection, candidate-universe mismatch rejection, positive/negative collision rejection, deterministic ordering, deterministic dry-run sample limits, and artifact hash stability.
- [x] 2.3 Add RED tests for mock batch construction, mock ranking loss behavior, invalid shape validation, and empty-batch behavior without torch/GPU requirements.
- [x] 2.4 Add RED tests for the dry-run trainer CLI outputs, artifact-freeze content, safety-check content, dataset summary, dry-run card, human brief, progress ledger, and preservation of MVP/mining/visual-backend import safety.

## 3. Training-Readiness Implementation

- [x] 3.1 Add `configs/train_lora_dry_run.json` and `configs/train_lora.local.example.json` with model identity, local model path, adapter output, hard-negative input, corpus/query/qrels paths, candidate universe, loss, hyperparameter, device, dry-run, and final-test safety fields.
- [x] 3.2 Add training-readiness config dataclasses/loading, strict type validation, path validation, `allow_final_test=false` enforcement, and `dry_run=true` enforcement for Phase 5A.
- [x] 3.3 Add a hard-negative triple loader that reads train/dev JSONL files, validates Phase 4 schema, validates query/page split boundaries from manifests, enforces candidate-universe identity, rejects negative-equals-positive records, and emits deterministic triples.
- [x] 3.4 Add CPU-safe mock batch construction, deterministic fake scoring, and mock contrastive/ranking loss helpers that do not import torch by default.
- [x] 3.5 Add `visdoc_retrieve.train_lora_dry_run` CLI orchestration for config parse, artifact hashing, dataset load, leakage checks, mock batch/loss computation, and report writing.

## 4. Evidence Outputs

- [x] 4.1 Emit `reports/training-readiness/artifact-freeze.json` with train/dev hard-negative hashes, corpus/query/qrels hashes, candidate universe, split policy, metric-definition reference, model revision value, timestamp, and final-test exclusion.
- [x] 4.2 Emit `reports/training-readiness/dataset-summary.json`, `dry-run-card.md`, and `safety-check.json` with explicit no-training/no-download/no-GPU/no-checkpoint/no-benchmark-claim boundaries.
- [x] 4.3 Generate a concise Chinese human brief under `docs/human-briefs/` that explains Phase 5A readiness, hard-negative triple flow, artifact freeze, dry-run checks, excluded future work, Phase 5B path, and evidence links.
- [x] 4.4 Update `reports/progress-ledger.yaml` with a Phase 5A entry and no real training, final-test metric, or benchmark-improvement claim.

## 5. Validation And Review

- [x] 5.1 Run the required MVP smoke, hard-negative mining CLI, training dry-run CLI, py_compile, pyproject parse, pytest, Ruff, mypy, OpenSpec strict validation, and `git diff --check`.
- [x] 5.2 Run a Reviewer subagent over the diff and fix Must Fix items only unless replanning is required.
- [x] 5.3 Commit, push `codex/add-training-readiness-phase-5a`, create a PR, and stop without merge, deploy, archive, training, A100 execution, model downloads, adapter checkpoint creation, final-test evaluation, or benchmark claims.
