## Context

The repository is an empty Git project. The external project brief defines VisDoc-Retrieve as a recruiter-facing algorithm project for page-level visual document retrieval using ColPali / ColQwen-style late interaction, but Phase 0 must only establish the maintainable repository foundation and validation baseline.

The first implementation change must therefore create enough structure for future OpenSpec phases without introducing data generation, retrieval models, evaluation metrics, or benchmark claims.

## Goals / Non-Goals

**Goals:**

- Create a minimal Python `src`-layout project skeleton.
- Establish README and AGENTS surfaces that preserve the project positioning and scope boundaries.
- Add placeholder directories for future configs, reports, and data documentation.
- Add a bounded progress ledger that can be replaced after each future OpenSpec change.
- Make local validation deterministic with `pytest`, `ruff`, `mypy`, and OpenSpec validation.

**Non-Goals:**

- No synthetic corpus generation.
- No page rendering, OCR extraction, manifest schemas, or retrieval datasets.
- No BM25, dense retrieval, hybrid retrieval, metrics, ColPali/ColQwen integration, embedding cache, hard-negative mining, LoRA/QLoRA training, or final reports.
- No chatbot UI, generic RAG app, Agent, browser automation workflow, citation safety system, or QA generation system.
- No benchmark result claims.

## Decisions

1. Use a minimal Python `src/visdoc_retrieve` layout.

   Rationale: future phases will add reusable package modules, and the `src` layout prevents tests from accidentally importing undeclared local modules from the repository root. The alternative, a flat package at repository root, is simpler initially but weaker as the project grows.

2. Keep Phase 0 validation CPU-only and dependency-light.

   Rationale: the bootstrap must pass on the local Mac without optional GPU/model dependencies. Future ColPali/ColQwen and A100 paths should be introduced behind separate OpenSpec changes. The alternative, adding optional model extras now, increases installation surface before there is a stable data/evaluation contract.

3. Treat the README as a claim boundary, not a result surface.

   Rationale: the project brief explicitly forbids improvement claims before frozen evaluation exists. Phase 0 README content should explain the intended algorithmic direction and state that no final results exist yet. The alternative, adding aspirational result tables, would create a stale or misleading recruiter surface.

4. Store the initial progress ledger under `reports/`.

   Rationale: `reports/` is the natural place for human-readable project state and later evidence artifacts. The ledger must be bounded and replaceable rather than an append-only diary. The alternative, placing it only in README, would mix operational state with public positioning.

## Risks / Trade-offs

- Over-scoping Phase 0 into data or retrieval work -> Keep tasks limited to repository skeleton and validation baseline.
- README becoming a marketing surface with unsupported claims -> Add explicit no-results wording and avoid metric numbers.
- Validation churn from heavy dependencies -> Use only lightweight dev tooling in this change.
- Future phases needing different package boundaries -> Keep Phase 0 modules minimal and avoid speculative abstractions.
