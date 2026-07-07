## Context

The repository now contains diagnostic MVP evidence, text baselines, a mock
visual late-interaction scaffold, hard-negative mining, training gates, A100
runtime gates, a reviewed tiny A100 LoRA runner proof, a dev-only pilot
evaluation harness, and a current project milestone narrative.

Those surfaces are deliberately bounded. The next risky transition is from
dev-only or tiny-runner evidence into final comparison language. Phase 6B
freezes the protocol before any longer dev training or final-test evaluation is
allowed.

## Goals / Non-Goals

**Goals:**

- Define final-test access gates before final-test files can be read.
- Define a comparison-table schema that can represent text baseline,
  zero-shot visual baseline, longer dev training, and final benchmark rows
  without fabricating unavailable metrics.
- Define a public claim checklist that blocks benchmark improvement claims
  unless the frozen protocol is satisfied.
- Provide reviewer-facing evidence that Phase 6B is protocol-only.

**Non-Goals:**

- No training or A100/GPU/SSH work.
- No model download, model inference, final-test read, final evaluation, or
  deployment.
- No model weights, adapter checkpoints, cache artifacts, private config, or
  exact private model path in git.
- No benchmark improvement, model superiority, or README result claim.

## Decisions

- Use a documentation-first protocol instead of executable final-test code.
  This avoids accidentally reading final-test data while still making the next
  implementation step unambiguous.
- Keep final-comparison evidence under `reports/final-comparison-protocol/`.
  This separates protocol-freeze evidence from training-pilot reports.
- Represent unavailable rows as `not_available`, `not_run`, or `blocked`
  rather than null-filled metric tables with ambiguous status.
- Require every final benchmark claim to reference a frozen protocol version,
  input manifest, candidate universe, final-test authorization, artifact
  hygiene scan, and reviewer checklist.
- Keep README wording unchanged in this phase unless a later phase explicitly
  updates public claims after final evaluation.

## Risks / Trade-offs

- Protocol-only work may feel indirect -> Mitigated by producing concrete
  schemas and checklists that later phases can execute against.
- Future training could still overclaim if it bypasses the checklist ->
  Mitigated by making the checklist a required evidence artifact.
- Final-test access rules can become stale -> Mitigated by requiring a later
  OpenSpec change before any final-test execution.
- Existing active completed OpenSpec changes remain in the backlog ->
  Mitigated by keeping this phase focused and leaving backlog cleanup for a
  separate archive-only step.

## Migration Plan

- Add the Phase 6B protocol docs, evidence JSON/Markdown, Human Brief, and
  progress-ledger entry.
- Validate locally without A100, network, model downloads, training, or final
  test access.
- Open a PR and stop without merge, deploy, or archive.

## Open Questions

- Which exact longer-dev training budget should be used after protocol freeze?
- Who authorizes final-test access when the repository is ready for a frozen
  final comparison?
