"""CLI entry point for the Phase 5D real-training backend wiring gate."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.training_pilot import (
    TrainingPilotConfig,
    TrainingPilotConfigError,
    TrainingPilotOutputs,
    load_training_pilot_config,
    run_training_pilot_gate,
)

__all__ = [
    "TrainingPilotConfig",
    "TrainingPilotConfigError",
    "TrainingPilotOutputs",
    "load_training_pilot_config",
    "main",
    "run_training_pilot_gate",
]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase 5D local-only pilot backend wiring gate."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    config_path = args.config if args.config.is_absolute() else repo_root / args.config
    try:
        config = load_training_pilot_config(config_path, repo_root=repo_root)
        result = run_training_pilot_gate(config, repo_root=repo_root)
    except TrainingPilotConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if result["status"] == "blocked":
        reasons = result.get("blocked_reasons", [])
        print(f"blocked: {reasons}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
