"""CLI entry point for deterministic hard-negative mining."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.data_schema import ValidationError
from visdoc_retrieve.hard_negatives import (
    load_hard_negative_config,
    run_hard_negative_mining,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run hard-negative mining from a committed JSON config."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        config = load_hard_negative_config(args.config)
        run_hard_negative_mining(config, repo_root=args.repo_root)
    except (ValueError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
