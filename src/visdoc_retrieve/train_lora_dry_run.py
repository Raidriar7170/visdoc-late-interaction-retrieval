"""CLI entry point for Phase 5A training-readiness dry runs."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.data_schema import ValidationError
from visdoc_retrieve.training_readiness import (
    TrainingReadinessConfigError,
    load_training_readiness_config,
    run_training_readiness_dry_run,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local-only training-readiness dry-run command."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        config = load_training_readiness_config(args.config)
        run_training_readiness_dry_run(config, repo_root=args.repo_root)
    except (TrainingReadinessConfigError, ValidationError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
