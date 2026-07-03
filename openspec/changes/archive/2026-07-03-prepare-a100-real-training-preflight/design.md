## Context

Phase 5D added import-safe backend wiring, but the first A100 inspection found
that the remote host has GPU/CUDA capacity without a confirmed VisDoc checkout,
without a known local ColPali / ColQwen weight directory, and without
`colpali_engine` importability in the checked Python environments. The user has
authorized A100 use for suitable GPU-heavy work, but all files created or
modified there must stay under `/mnt/data/minghongsun`.

This phase is a setup/preflight checkpoint, not a training checkpoint. It
should answer whether the remote environment is ready for a later tiny pilot and
what remains blocked, without creating private or misleading public evidence.

## Goals / Non-Goals

**Goals:**
- Ensure the remote repo checkout, env/cache/log roots, and preflight artifacts
  live under `/mnt/data/minghongsun`.
- Check A100 GPU visibility and identify safe idle GPU candidates without
  interrupting other users' work.
- Check Python dependency importability for the Phase 5D backend path.
- Check whether a user-provided local model path exists, while committing only
  redacted path summaries.
- Commit sanitized Phase 5E evidence and a Chinese Human Brief that state
  `preflight_ready`, `blocked`, or `needs_user_input` truthfully.

**Non-Goals:**
- Do not run `train_lora_pilot` in real-training mode.
- Do not download model weights or resolve remote model IDs.
- Do not install system packages or write to `/root`, `/tmp`, or other users'
  directories.
- Do not create adapters, checkpoints, cache artifacts, logs, final-test
  metrics, or benchmark-improvement claims.
- Do not archive OpenSpec, deploy, or merge as part of this phase.

## Decisions

1. **Use a dedicated sanitized preflight artifact instead of raw SSH logs.**
   Raw remote logs may contain hostnames, process IDs, private paths, or other
   operational details. The committed artifact will keep only status flags,
   coarse GPU summaries, dependency booleans, and redacted path summaries.

2. **Treat missing `colpali_engine` and missing model path as blockers, not
   reasons to force setup.** A Python package install under the allowed root is
   permitted only if it can be done without system writes or model downloads.
   If a required model path is unknown, the phase records `needs_user_input`
   rather than guessing or downloading a model.

3. **Keep remote setup under one project root.** The expected remote project
   root is `/mnt/data/minghongsun/visdoc-late-interaction-retrieval`; optional
   venv/cache locations should also be under that root or another explicit
   `/mnt/data/minghongsun/...` path.

4. **Separate idle-GPU observation from job launch.** The preflight can observe
   memory and utilization, but it must not reserve, kill, signal, preempt, or
   start GPU work. A later accepted phase must explicitly choose
   `CUDA_VISIBLE_DEVICES` before any job launch.

## Risks / Trade-offs

- Missing remote Git credentials or network access may block a clean checkout.
  -> Mitigation: record the checkout as blocked and do not fall back to secret
  copying or untracked private state.
- Installing Python packages could write outside the allowed root if run from
  the base environment. -> Mitigation: use only an allowed-root venv/cache, or
  record `optional_dependency_missing` without installing.
- A local model path may be private or unknown. -> Mitigation: require an exact
  user-provided path for readiness, commit only existence/redaction status, and
  do not scan broad private directories beyond agreed roots.
- GPU process ownership may be unclear. -> Mitigation: only recommend GPUs
  that appear idle by memory/utilization and stop before launch if safety is
  ambiguous.
