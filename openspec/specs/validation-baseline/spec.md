# validation-baseline Specification

## Purpose
Documents the local validation baseline that keeps repository changes
reproducible without data downloads, GPU hardware, model downloads, or network
services unless a later OpenSpec change expands that contract.
## Requirements
### Requirement: Local validation commands
The repository SHALL define and pass a local validation baseline consisting of `pytest -q`, `ruff check .`, `mypy src`, and `openspec validate --all --strict`.

#### Scenario: Validation baseline passes
- **WHEN** Phase 0 is applied in the repository root
- **THEN** `pytest -q`, `ruff check .`, `mypy src`, and `openspec validate --all --strict` all complete successfully

### Requirement: Minimal smoke tests
The repository SHALL include minimal tests that verify the Python package can be imported without requiring data files, GPU hardware, model downloads, or network access.

#### Scenario: Smoke tests are local-only
- **WHEN** `pytest -q` runs after Phase 0 is applied
- **THEN** the tests pass using only local CPU execution and do not require ColPali, ColQwen, embedding models, PDF rendering, datasets, or A100 access

### Requirement: Tool configuration lives in project metadata
The repository SHALL configure linting, typing, and test discovery through `pyproject.toml` or equivalent project metadata committed in the repository.

#### Scenario: Tooling is reproducible from metadata
- **WHEN** a developer inspects the Phase 0 repository
- **THEN** the commands for pytest, Ruff, and mypy are discoverable from committed project metadata and do not rely on unstated local IDE configuration
