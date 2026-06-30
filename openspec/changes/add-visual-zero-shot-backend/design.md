## Context

VisDoc-Retrieve has a one-command diagnostic MVP pipeline that ranks the fixed
synthetic smoke `dev` split with deterministic text baselines and a CPU-only
`mock_visual` MaxSim scaffold. The existing MVP artifacts are intentionally
diagnostic and state that no real ColPali / ColQwen execution occurred.

This change adds a separate optional real-backend checkpoint. It must let a
user with local visual-model weights and a prepared local environment run a
small visual zero-shot smoke entry point, while keeping default CI and the MVP
pipeline mock-only, CPU-only, network-free, and unchanged.

## Goals / Non-Goals

**Goals:**

- Add an import-safe local visual-model backend adapter surface.
- Require explicit config to select a real backend.
- Validate backend config, local model path, device, batch size, cache path,
  corpus path, query path, and qrels path.
- Provide `--check-config` and `--dry-run` modes that never import heavyweight
  model libraries or download weights.
- Fail clearly when a configured local model path is missing or the optional
  runtime is unavailable.
- Preserve the deterministic `MockVisualRetriever` and existing MVP command.
- Add a cache schema that can hold real query/page token embeddings and remains
  compatible with MaxSim scoring.

**Non-Goals:**

- Adding model weights, downloading ColPali / ColQwen / BGE /
  sentence-transformers weights, requiring GPU, using the A100, training,
  hard-negative mining, LoRA/QLoRA, final-test evaluation, benchmark result
  tables, benchmark improvement claims, chatbot/RAG behavior, deployment, or
  CI execution of the optional real smoke.

## Decisions

1. Keep the real visual smoke as a new CLI instead of extending the default MVP
   command.
   - Rationale: the MVP command is established evidence for deterministic mock
     diagnostics. A separate entry point avoids silently changing its runtime
     requirements or claims.
   - Alternative considered: add real visual methods to `configs/mvp.json`.
     That would make the default MVP surface ambiguous and increase CI risk.

2. Add lazy local-backend classes with config preflight before runtime imports.
   - Rationale: importing `visdoc_retrieve` modules in tests must not import
     optional model packages, trigger network access, or inspect GPUs.
   - Alternative considered: add optional dependencies to `pyproject.toml`.
     That would widen default installation and validation.

3. Treat missing model paths and missing optional runtime dependencies as clear
   errors, not skipped success.
   - Rationale: the checkpoint is about a truthful real-backend boundary. If a
     real run cannot happen, the CLI must say why and exit non-zero unless the
     user requested `--check-config` or `--dry-run`.
   - Alternative considered: silently falling back to `mock_visual`. That would
     risk reporting mock evidence as real visual retrieval.

4. Use a generic token-embedding cache schema for optional real embeddings.
   - Rationale: MaxSim only needs query/page token matrices and metadata. A
     small JSON schema is testable locally without committing caches or model
     outputs.
   - Alternative considered: persist framework-native tensors. That would
     introduce optional dependency and compatibility issues in default tests.

5. Keep real execution local-only and `local_files_only`.
   - Rationale: model IDs may be useful for local Hugging Face cache lookup,
     but this phase must not download weights or require network.
   - Alternative considered: allow automatic downloads when a model ID is set.
     That violates the phase boundary.

## Risks / Trade-offs

- Real backend scaffold may be mistaken for benchmark evidence -> Mitigation:
  docs, config, CLI output, ledger, and human brief state optional local smoke
  only and no benchmark claim.
- Optional runtime APIs differ across ColPali / ColQwen installations ->
  Mitigation: keep the adapter boundary small, import-safe, and explicit; fail
  clearly when the local runtime cannot be loaded.
- Device config may imply GPU use -> Mitigation: GPU is allowed only when the
  user explicitly sets a device such as `cuda:0`; default examples stay CPU and
  CI never runs real execution.
- Cache files could be committed accidentally -> Mitigation: example cache path
  points under an ignored local cache directory and tests assert no committed
  model/cache artifacts are required.

## Migration Plan

No migration is required. Existing MVP, text, and visual-smoke commands remain
unchanged. Users who want real visual zero-shot smoke copy the local example
config, set local paths, install their optional runtime outside the default
project contract, and run the new CLI explicitly.

## Open Questions

- Which exact local ColPali / ColQwen runtime package should become the first
  fully supported execution adapter in a later phase?
- Should later real runs write a separate evidence bundle under
  `reports/visual-zero-shot/` after the user provides a local model environment?
