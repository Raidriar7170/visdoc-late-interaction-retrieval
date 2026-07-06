"""CLI entry point for Phase 5K dev-only pilot evaluation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.dev_only_pilot_eval import (
    DevOnlyPilotEvalConfigError,
    load_dev_only_pilot_eval_config,
    run_dev_only_pilot_eval,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase 5K dev-only evaluation harness."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    config_path = args.config if args.config.is_absolute() else repo_root / args.config
    try:
        config = load_dev_only_pilot_eval_config(config_path)
        run_dev_only_pilot_eval(config, repo_root=repo_root)
    except DevOnlyPilotEvalConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
