# opsx-auto Prerequisites

This repository now contains the repo-local prerequisites for a later
`unattended-local-core` setup. This page documents preparation only; it does
not activate `$opsx-auto` and does not initialize the runtime store.

## Prepared Files

- `.opsx-auto-config/unattended-local.json`
- `.opsx-auto-config/contract.json`
- `.opsx-auto-config/validation-policy.json`
- `scripts/validate-local-core.sh`
- `tests/test_opsx_auto_prerequisites.py`

## Validation Wrapper

The pinned validation wrapper is:

```bash
bash scripts/validate-local-core.sh
```

It runs the local baseline in a fixed order:

```text
python -m pytest -q
ruff check .
mypy src
openspec validate --all --strict
git diff --check
```

It does not install packages, download models, require GPU or A100 hardware,
mutate `.opsx-auto/`, stage files, commit, merge, push, archive, deploy, or use
network services.

## Remaining Manual Bootstrap

The prepared files are not enough to start the autonomous loop in this current
main worktree. Before `init-store` can succeed, the human-controlled setup still
needs:

1. Create a real initial commit for the repository.
2. Create or switch into a dedicated linked Git worktree.
3. Verify the dedicated worktree is clean and has a real HEAD commit.
4. Run:

```bash
python /Users/raidriar/.codex/skills/opsx-auto/scripts/opsx-auto-runtime.py init-store --repo-root . --mode unattended-local-core
```

5. Provide a bounded phase manifest in `.opsx-auto-inbox/`.
6. Run `resolve` only after `init-store` succeeds.

## Boundaries

This preparation does not implement text retrieval baselines. It also does not
run ColPali or ColQwen, generate hard-negative triples, start LoRA or QLoRA
training, run final test evaluation, claim benchmark improvement, create a
worktree, stage, commit, merge, push, archive, or initialize `.opsx-auto/`.
