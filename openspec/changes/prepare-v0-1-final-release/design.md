## Context

`main` is clean after PR #29 and has no active OpenSpec changes. The project is
ready for a `v0.1.0` final-tag/release preparation pass, but actual tag creation
and GitHub Release publication should remain explicit confirmation gates.

The release must carry the same truth boundary as the final comparison:
`no_clear_improvement_claim`, no retuning after final-test access, no
unavailable-system metric fabrication, and no real visual-model performance
claim from `mock_visual`.

## Goals / Non-Goals

**Goals:**

- Prepare reviewable `v0.1.0` release notes.
- Provide a tag checklist with preflight checks and explicit manual commands.
- Record machine-readable readiness evidence.
- Make release-prep evidence discoverable from README, evidence index, and the
  progress ledger.

**Non-Goals:**

- Do not create or push an annotated tag.
- Do not create or publish a GitHub Release.
- Do not deploy.
- Do not train, tune, use A100/SSH/GPU, download models, rerun final comparison,
  read final-test labels/qrels, or modify final metrics/rankings/manifest.
- Do not add benchmark improvement claims.

## Decisions

- **Use `v0.1.0` as the planned release label.** The project has reached a
  coherent final benchmark/evidence state but still carries explicit limitations
  and no clear improvement claim.
- **Keep release execution manual.** The checklist documents the commands, but
  the PR does not run them. The target commit is the future post-merge `main`
  commit, not the current feature-branch commit.
- **Keep release notes evidence-first.** The notes link to final report,
  manifest, metrics, claim checklist, no-retune pledge, evidence index, project
  card, resume bullets, and interview talking points.
- **Record validation scope honestly.** Full `pytest -q` is not used here
  because `tests/test_final_comparison_run.py` executes final-comparison logic
  against temp outputs and reads the final split.

## Risks / Trade-offs

- **Risk: release prep is mistaken for publication.** Mitigation: every release
  artifact states that the tag and GitHub Release are not created yet.
- **Risk: release notes overclaim results.** Mitigation: the release notes keep
  `no_clear_improvement_claim` and unavailable-system status near the top.
- **Risk: readiness report has stale target commit after merge.** Mitigation:
  mark the planned tag target as `post_merge_main_head`, with current base HEAD
  recorded as context.
