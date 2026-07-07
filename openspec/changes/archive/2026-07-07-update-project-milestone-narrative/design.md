## Context

Phase 5K is now merged and archived on `main`. The repository contains
diagnostic MVP evidence, text baselines with candidate-universe metadata,
mock visual late-interaction scaffolding, optional visual backend scaffolding,
hard-negative mining, training readiness and pilot safety gates, A100 runtime
and model-path gate evidence, a reviewed tiny LoRA runner proof, and a
dev-only pilot evaluation harness.

The README still reads as if the project is near Phase 3A. That mismatch can
mislead external readers in two directions: understating the implemented
infrastructure, or overstating tiny/dev-only evidence as model performance.

## Goals / Non-Goals

**Goals:**

- Make the GitHub homepage accurately summarize the current milestone.
- Provide a single evidence index for reports, Human Briefs, and OpenSpec
  archives.
- Provide a recruiter-facing milestone brief that is useful but conservative.
- Preserve strict public-claim boundaries around final test, benchmark
  improvement, model weights, adapters, private paths, and tiny runner proof.
- Scan for bidi Unicode controls and keep Chinese text intact.

**Non-Goals:**

- No source-code behavior changes.
- No metrics changes or new result tables.
- No A100, SSH, GPU, training, model download, or final-test execution.
- No OpenSpec archive during Phase 6A unless this documentation-only change is
  later explicitly completed and archived in a separate closeout.

## Decisions

- Keep this as a documentation-only OpenSpec change. This makes the phase
  auditable without changing retrieval or training behavior.
- Add `docs/evidence-index.md` as the stable public evidence map rather than
  burying links only in README. The README can stay concise while the index
  remains detailed.
- Add a Chinese Human Brief for recruiter-facing review because existing
  project briefs are already under `docs/human-briefs/` and are the user's
  preferred human truth surface.
- Use negative boundary statements explicitly: "not final benchmark",
  "final test not used", "no benchmark improvement claim", and "no committed
  model weights/adapters".
- Treat Unicode-control scanning as a validation artifact in the progress
  ledger. Chinese characters are allowed; bidi control characters are not.

## Risks / Trade-offs

- Overclaim risk -> Mitigated by stating that tiny `max_steps=1` /
  `sample_limit=1` evidence is a runner proof, not benchmark performance.
- Evidence sprawl -> Mitigated by centralizing paths in `docs/evidence-index.md`
  and referencing OpenSpec archives.
- README verbosity -> Mitigated by keeping status concise and pointing to the
  evidence index for details.
- Validation side effects -> Existing CLI validations may regenerate older
  training-pilot artifacts. Any such unrelated diffs must be reverted before
  commit.
