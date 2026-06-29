"""CLI entry point for the diagnostic VisDoc-Retrieve MVP pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.mvp_pipeline import load_mvp_config, run_mvp_pipeline


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MVP pipeline from a committed JSON config."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    config = load_mvp_config(args.config)
    run_mvp_pipeline(config, repo_root=args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
