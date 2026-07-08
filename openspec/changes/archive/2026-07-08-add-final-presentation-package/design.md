## Context

The repository has completed Phase 6D under the frozen
`phase-6b-final-comparison-protocol/v1` contract. The final artifacts already
record that the final test was read once, no training or tuning was performed,
and the claim checklist concluded `no_clear_improvement_claim`.

Phase 7A is not another evaluation phase. It is a documentation and evidence
packaging phase that translates the existing final evidence into public-facing
materials for GitHub readers, recruiters, and interviewers.

## Goals / Non-Goals

**Goals:**

- Make the README final status accurate after Phase 6D.
- Provide recruiter-facing and interview-facing summaries that cite evidence
  rather than inventing stronger claims.
- Make final comparison evidence discoverable from the evidence index.
- Preserve the no-retune and no-overclaim boundaries in every presentation file.
- Keep the change archiveable as an OpenSpec documentation milestone.

**Non-Goals:**

- Do not rerun the final comparison.
- Do not read or modify final-test labels/qrels.
- Do not train, tune, download models, use A100/GPU/SSH, or change retrieval
  behavior.
- Do not modify final metrics, rankings, run manifest, candidate universe, or
  metric definitions.
- Do not claim benchmark improvement, model superiority, or real visual-model
  performance from `mock_visual`.

## Decisions

- **Use existing Phase 6D artifacts as the source of truth.** The final
  comparison report, run manifest, metrics, claim checklist, and no-retune
  pledge are authoritative. Presentation docs link to them instead of
  duplicating more numbers than needed.
- **Keep public wording conservative.** The materials can say the project built
  a reproducible evaluation pipeline and executed a one-time final comparison,
  but they must also say the final claim checklist does not support a clear
  improvement claim.
- **Separate systems that ran from systems that were unavailable.** `bm25`,
  `lexical_cosine`, `bm25_lexical_rrf`, and `mock_visual` ran. The
  `tiny_lora_adapter` and `zero_shot_visual_backend` rows remain
  `not_available`; their metrics are not fabricated.
- **Treat `mock_visual` as scaffold evidence only.** It remains a deterministic
  MaxSim scaffold, not a real visual model result.

## Risks / Trade-offs

- **Risk: recruiter-facing prose overstates results.** Mitigation: put the
  result boundary near the top of each presentation document and avoid
  percentage-uplift wording.
- **Risk: README becomes stale again after future work.** Mitigation: point to
  durable evidence paths and progress-ledger status instead of relying on only
  prose.
- **Risk: validation command conflicts with no-final-rerun boundary.**
  Mitigation: do not run the production final-comparison command; if a test
  command would execute final-comparison logic, report that boundary explicitly.
