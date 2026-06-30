"""CLI for optional local visual zero-shot smoke preflight."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from visdoc_retrieve.visual_zero_shot import (
    VisualZeroShotConfigError,
    check_visual_zero_shot_config,
    load_visual_zero_shot_config,
)
from visdoc_retrieve.visual_zero_shot_backend import (
    LocalVisualModelBackend,
    VisualZeroShotBackendError,
)


def main(argv: list[str] | None = None) -> int:
    """Run the visual zero-shot CLI."""

    parser = argparse.ArgumentParser(
        description="Optional local visual zero-shot retrieval preflight."
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path)
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        config = load_visual_zero_shot_config(args.config)
        check_visual_zero_shot_config(config, repo_root=args.repo_root)
    except (OSError, VisualZeroShotConfigError) as exc:
        print(f"visual zero-shot config error: {exc}", file=sys.stderr)
        return 2

    if args.check_config:
        print("visual zero-shot config check passed")
        return 0
    if args.dry_run:
        print("visual zero-shot dry run passed; real model execution not started")
        return 0

    try:
        backend = LocalVisualModelBackend(config.backend)
        backend.run()
    except VisualZeroShotBackendError as exc:
        print(f"visual zero-shot runtime error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
