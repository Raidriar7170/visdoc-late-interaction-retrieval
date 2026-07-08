# VisDoc-Retrieve Interview Talking Points

## Why Visual Late Interaction

The target problem is visually rich document retrieval, where relevant evidence
may live in layout, tables, figures, or OCR-damaged regions. Visual late
interaction is attractive because it can preserve token-level or patch-level
matching signals instead of collapsing a page into one embedding too early.

In this project, the real visual model row was not available for final
benchmarking. The implemented `mock_visual` path should be described as a
deterministic MaxSim scaffold that proves ranking, caching, and evaluation
plumbing, not as real visual-model performance.

## Why Hard-Negative Mining

Hard negatives make retrieval training more realistic by pairing queries with
plausible but wrong pages. The project mines train/dev hard-negative artifacts
from diagnostic surfaces and explicitly keeps final test out of that process.

The main engineering value is the data-contract discipline: mined examples are
traceable, split-aware, and separated from final evaluation.

## Why No-Retune Pledge

The no-retune pledge protects the final benchmark from result-driven iteration.
After the Phase 6D final run, the repository records that no tuning,
retrieval-pipeline changes, metric-definition changes, candidate-universe
changes, final-label changes, or result-driven reruns are allowed.

This is the difference between an engineering benchmark and a dashboard that
can be silently optimized after seeing the answer key.

## How To Explain Mixed / No Clear Improvement

The final claim checklist says `no_clear_improvement_claim`. That is not a
failure of the process; it is the process doing its job. The project produced a
credible final comparison and refused to overstate unsupported results.

The systems that ran were deterministic text baselines and a mock visual
scaffold. The real visual backend and tiny LoRA adapter were `not_available`,
so the final report does not fabricate metrics for them.

## How To Explain The Tiny A100 Runner Proof

The tiny A100 runner proof used `max_steps=1` and `sample_limit=1`. It is useful
pipeline evidence: it shows that a reviewed backend runner can cross basic
runtime gates. It is not a training result, not a benchmark row, and not a
model-performance improvement.

## What I Would Improve Next

- Add a real local visual backend artifact that can be evaluated under the
  frozen protocol without downloading models during the benchmark phase.
- Run longer controlled dev-only training before any future final benchmark,
  with a new protocol and no access to final labels during tuning.
- Expand the corpus beyond synthetic smoke data while preserving split and
  candidate-universe contracts.
- Add reviewer approval before making any public benchmark improvement claim.

## Short Answer For Recruiters

I built a document-retrieval evaluation project that is valuable because of its
engineering discipline: clear data contracts, reproducible baselines, training
gates, final-run governance, and honest claim boundaries. The final result does
not support a clear improvement claim, and I intentionally preserved that truth
instead of tuning after final-test access.
