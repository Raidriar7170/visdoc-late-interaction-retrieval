## Why

VisDoc-Retrieve needs a clean OpenSpec-managed foundation before any retrieval, data, model, or training work begins. This change establishes a recruiter-facing multimodal document retrieval project skeleton while preserving the non-negotiable boundary that no benchmark result is claimed before a frozen evaluation exists.

## What Changes

- Initialize the repository as a Python project for visual document retrieval with late interaction.
- Add the minimal Phase 0 project surfaces: README, AGENTS instructions, package metadata, source/test directories, config/report/data placeholders, and a bounded progress ledger.
- Establish local validation commands for tests, linting, typing, and OpenSpec validation.
- Document project positioning as page-level multimodal retrieval and ranking, not a chatbot, generic RAG app, Agent, browser automation system, or QA generation system.
- Keep all data generation, retrieval models, metrics implementations, ColPali/ColQwen inference, hard-negative mining, LoRA training, and benchmark result claims out of this change.

## Capabilities

### New Capabilities

- `project-bootstrap`: Defines the Phase 0 repository skeleton, project positioning, README boundaries, and bounded progress ledger for VisDoc-Retrieve.
- `validation-baseline`: Defines the required local validation surface for the Phase 0 skeleton.

### Modified Capabilities

- None.

## Impact

- Affected repository surfaces: `README.md`, `AGENTS.md`, `pyproject.toml`, `src/visdoc_retrieve/`, `tests/`, `configs/`, `reports/`, `data/README.md`, and OpenSpec artifacts.
- No runtime retrieval APIs, model dependencies, generated datasets, benchmark reports, or training scripts are introduced in this change.
