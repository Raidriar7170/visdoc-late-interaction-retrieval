## Context

Phase 5K follows the archived Phase 5I gated pilot attempt and Phase 5J
reviewed tiny runner. It must make the dev-only evaluation surface
reproducible without depending on A100 access, committed adapters, model
weights, final-test data, or benchmark claims.

The current repository already has sanitized Phase 5I/5J training-pilot
evidence and baseline reports. Phase 5K should consume those public artifacts
and produce another public artifact set that is explicit about scope:
dev-only, pilot sanity only, not final benchmark.

## Goals

- Add an import-safe dev-only evaluation harness with a deterministic local CLI.
- Read sanitized pilot manifests and dev split hard-negative artifacts only.
- Never read final-test files or paths.
- Produce public-safe evidence for environment, safety, run-card,
  adapter-manifest, dev-only eval, comparison schema, Human Brief, and
  progress-ledger.
- Preserve existing MVP, hard-negative mining, dry-run, and blocked pilot
  validation commands.

## Non-Goals

- No A100 launch in the local harness path.
- No model download or network access.
- No final-test evaluation.
- No benchmark improvement claim.
- No committed model weights, adapter checkpoints, caches, private local
  config, or exact private model path.
- No README result claim.
- No OpenSpec archive, merge, or deploy in this phase.

## Design

### Harness Inputs

The harness reads a checked-in JSON config whose defaults point at public
sanitized artifacts:

- `reports/training-pilot/phase-5j-adapter-manifest.sanitized.json`
- `data/derived/hard_negatives/dev.jsonl`
- optional text baseline summary from `reports/progress-ledger.yaml`
- optional visual baseline summary from `reports/progress-ledger.yaml`

The config includes a `final_test_paths` deny-list. The harness checks that no
input path contains final-test markers and records this in safety evidence.

### Adapter Availability

The Phase 5J sanitized manifest can report that an adapter was created in an
ignored `.local/` artifact directory, but that directory is intentionally not
committed. Phase 5K therefore records:

- `tiny_pilot_adapter.status=not_available`
- `adapter_checkpoint_committed=false`
- `metrics` fields remain `null`

This prevents confusing a prior tiny optimizer step with reusable committed
model evidence.

### Dev-Only Comparison Schema

The comparison schema is a contract, not a benchmark result. It may include
schema-compatible entries for:

- text baseline
- zero-shot visual baseline if a report is available
- tiny pilot adapter availability/status

Entries without usable metrics stay `not_available` or `schema_only`. The
schema must state `final_test_used=false`, `benchmark_improvement_claim=false`,
and `pilot_loss_reported_as_model_improvement=false`.

### Evidence Generation

The CLI writes:

- `reports/training-pilot/phase-5k-environment-check.json`
- `reports/training-pilot/phase-5k-safety-check.json`
- `reports/training-pilot/phase-5k-blocked-run-card.md`
- `reports/training-pilot/phase-5k-adapter-manifest.sanitized.json`
- `reports/training-pilot/phase-5k-dev-only-eval.json`
- `reports/training-pilot/phase-5k-comparison-schema.json`
- `docs/human-briefs/2026-07-06-dev-only-pilot-evaluation.html`
- `reports/progress-ledger.yaml` Phase 5K entry

Because A100 SSH is currently unavailable in the local execution context, the
Phase 5K run-card should truthfully record `tiny_pilot_status=skipped` or
`blocked` rather than implying a new pilot was run.

## Risks

- **Dev-only sanity is misread as benchmark improvement** -> evidence must keep
  explicit no-claim booleans and Human Brief wording.
- **Sanitized adapter path is misread as a committed checkpoint** -> adapter
  status must be `not_available` unless a committed public artifact exists,
  which this phase forbids.
- **Final test files are accidentally read** -> deny-list path checks and tests
  must fail closed.
