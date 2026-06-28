#!/bin/bash
set -eu

python -m pytest -q
ruff check .
mypy src
openspec validate --all --strict
git diff --check
