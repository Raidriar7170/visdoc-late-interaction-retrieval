## Why

The repository homepage and evidence surfaces still describe an earlier MVP-era
state even though Phase 5K has been merged and archived. A bounded milestone
narrative update is needed so external readers can understand the current
project maturity without confusing dev-only or tiny-runner evidence for final
benchmark results.

## What Changes

- Update `README.md` current status and boundary language to reflect the
  completed diagnostic pipeline, candidate-universe, mock visual scaffold,
  optional visual backend, A100 gates, hard-negative mining, training safety
  gates, reviewed tiny LoRA runner proof, and Phase 5K dev-only evaluation
  harness.
- Add a project evidence index that maps each milestone to the authoritative
  reports, briefs, and OpenSpec archive locations.
- Add a recruiter-facing milestone brief that explains what is demonstrable,
  what is not a final result, and why tiny-runner/dev-only evidence must not be
  read as benchmark performance.
- Add a Phase 6A progress-ledger entry and run Unicode-control scanning across
  Markdown, YAML, and JSON files.
- Do not change metrics, run training, use A100, run final test, deploy, or add
  benchmark improvement claims.

## Capabilities

### New Capabilities

- `project-milestone-narrative`: Documentation-only project milestone
  narrative, evidence-index, and public-claim boundary contract.

### Modified Capabilities

- None.

## Impact

- Affected files are documentation, OpenSpec planning artifacts, and
  `reports/progress-ledger.yaml`.
- No source code, configs, training data, model artifacts, checkpoints, caches,
  final-test metrics, or benchmark claims are introduced.
